from typing import Optional
from loguru import logger
from modules.chat.domain.entities import ChatSession, ChatMessage, MessageRole
from modules.chat.domain.ports import ILLMProvider, IMichiApiPort, IChatRepository

class ProcessUserMessageUseCase:
    def __init__(
        self, 
        llm_provider: ILLMProvider,
        michi_api: IMichiApiPort,
        repository: IChatRepository
    ):
        self.llm_provider = llm_provider
        self.michi_api = michi_api
        self.repository = repository

    async def execute(
        self, 
        session_id: str, 
        user_id: str, 
        org_id: str, 
        content: str,
        jwt: str
    ) -> str:
        # 1. Récupérer ou créer la session
        session = await self.repository.get_session(session_id)
        if not session:
            session = ChatSession(session_id=session_id, user_id=user_id, org_id=org_id)
        
        session.add_message(MessageRole.USER, content)
        if not session.title:
            session.title = content[:60] + ("..." if len(content) > 60 else "")
            
        await self.repository.save_session(session)
        
        # 2. Résumé pour mémoire (Phase 2)
        await self._summarize_if_needed(session)
        
        # 3. Injection du résumé dans le contexte
        messages_with_context = list(session.messages)
        if session.metadata.get("summary"):
            summary_msg = ChatMessage(role=MessageRole.SYSTEM, content=f"Résumé des échanges précédents : {session.metadata['summary']}")
            messages_with_context.insert(0, summary_msg)

        # 4. Boucle de raisonnement (Reasoning Loop) avec Client MCP et repli legacy
        # On permet jusqu'à 3 tours d'outils pour éviter les boucles infinies
        from mcp.client.sse import sse_client
        from mcp import ClientSession
        import os
        import json
        
        mcp_url = os.getenv("MCP_SERVER_URL", "http://localhost:8002/mcp/sse")
        headers = {
            "Authorization": f"Bearer {jwt}",
            "michi-org-id": org_id
        }
        
        try:
            logger.info(f"[Assistant] Connecting to MCP server at {mcp_url}...")
            async with sse_client(url=mcp_url, headers=headers) as (read, write):
                async with ClientSession(read, write) as mcp_session:
                    await mcp_session.initialize()
                    
                    # Récupérer les outils dynamiques du serveur MCP
                    tools_list = await mcp_session.list_tools()
                    mcp_tools = tools_list.tools
                    logger.debug(f"[Assistant] Registered {len(mcp_tools)} tools from MCP server.")
                    
                    for _ in range(3):
                        response = await self.llm_provider.generate_response(
                            messages_with_context,
                            tools=mcp_tools
                        )
                        
                        # Si c'est du texte simple, on a fini
                        if isinstance(response, str):
                            session.add_message(MessageRole.ASSISTANT, response)
                            await self.repository.save_session(session)
                            return response
                        
                        # Sinon, c'est un appel d'outil (Tool Call)
                        for tool_call in response:
                            func_name = tool_call["function"]["name"]
                            args_str = tool_call["function"]["arguments"]
                            args = json.loads(args_str) if args_str else {}
                            
                            logger.info(f"[Assistant MCP Client] Executing MCP tool: {func_name} with args: {args}")
                            
                            # Appeler l'outil sur le serveur MCP
                            mcp_result = await mcp_session.call_tool(func_name, args)
                            
                            # Extraire la réponse texte de l'outil
                            text_contents = []
                            for content in mcp_result.content:
                                if hasattr(content, "text"):
                                    text_contents.append(content.text)
                                elif isinstance(content, dict) and "text" in content:
                                    text_contents.append(content["text"])
                                    
                            result_data = "\n".join(text_contents)
                            logger.debug(f"[Assistant MCP Client] Tool result: {result_data[:200]}...")
                            
                            # Ajouter le résultat au contexte
                            session.add_message(MessageRole.SYSTEM, f"RÉSULTAT DE {func_name}: {result_data}")
        except Exception as mcp_err:
            logger.warning(f"[Assistant MCP Client] MCP connection failed: {mcp_err}. Falling back to legacy hardcoded tools.")
            
            # Repli sur l'ancienne boucle d'exécution en direct (legacy)
            for _ in range(3):
                response = await self.llm_provider.generate_response(messages_with_context)
                
                # Si c'est du texte simple, on a fini
                if isinstance(response, str):
                    session.add_message(MessageRole.ASSISTANT, response)
                    await self.repository.save_session(session)
                    return response
                
                # Sinon, c't un appel d'outil (Tool Call)
                for tool_call in response:
                    func_name = tool_call["function"]["name"]
                    args_str = tool_call["function"]["arguments"]
                    args = json.loads(args_str) if args_str else {}
                    
                    logger.info(f"[Assistant Legacy Fallback] Executing legacy tool: {func_name} with args: {args}")
                    
                    # Exécution réelle en direct (legacy)
                    result_data = "{}"
                    if func_name == "get_inventory":
                        data = await self.michi_api.get_inventory_status(org_id, jwt, filters=args)
                        result_data = str(data)
                    elif func_name == "get_alerts":
                        data = await self.michi_api.get_forecasting_alerts(org_id, jwt, filters=args)
                        result_data = str(data)
                    
                    session.add_message(MessageRole.SYSTEM, f"RÉSULTAT DE {func_name}: {result_data}")

        # Fallback si trop de tours
        await self.repository.save_session(session)
        return "J'ai récupéré beaucoup d'informations, mais je m'y perds un peu. Pouvez-vous préciser votre question ?"

    async def _summarize_if_needed(self, session: ChatSession):
        """Résume la session si elle dépasse 10 messages pour garder le contexte."""
        if len(session.messages) <= 10:
            return
        
        # Si on a déjà un résumé récent, on ne recommence pas à chaque message
        if session.metadata.get("summary_last_msg_count") == len(session.messages):
            return

        logger.info(f"[Assistant] Summarizing session {session.session_id}")
        prompt = "Résume brièvement la conversation précédente en soulignant les points clés et les décisions prises. Sois très concis."
        # On utilise le LLM pour résumer
        summary = await self.llm_provider.generate_response(
            session.messages[:-1] + [ChatMessage(role=MessageRole.USER, content=prompt)]
        )
        
        if isinstance(summary, str):
            session.metadata["summary"] = summary
            session.metadata["summary_last_msg_count"] = len(session.messages)

    async def execute_stream(
        self, 
        session_id: str, 
        user_id: str, 
        org_id: str, 
        content: str,
        jwt: str
    ):
        # 1. Récupérer ou créer la session
        session = await self.repository.get_session(session_id)
        if not session:
            session = ChatSession(session_id=session_id, user_id=user_id, org_id=org_id)
        
        session.add_message(MessageRole.USER, content)
        
        if not session.title:
            session.title = content[:60] + ("..." if len(content) > 60 else "")
            
        # Sauvegarde immédiate pour garantir la visibilité dans l'historique
        await self.repository.save_session(session)

        # 2. Résumé pour mémoire (Phase 2)
        await self._summarize_if_needed(session)
        
        # 3. Injection du résumé dans le contexte si présent
        messages_with_context = list(session.messages)
        if session.metadata.get("summary"):
            summary_msg = ChatMessage(
                role=MessageRole.SYSTEM, 
                content=f"Résumé des échanges précédents : {session.metadata['summary']}"
            )
            # On insère le résumé après le système prompt (ou au début si pas de système)
            messages_with_context.insert(0, summary_msg)
        
        # 4. Boucle de raisonnement (Simplifiée pour le stream)
        full_reply = ""
        try:
            async for chunk in self.llm_provider.stream_response(messages_with_context):
                full_reply += chunk
                yield chunk
        finally:
            # 5. Sauvegarde finale (toujours exécutée, même en cas d'erreur ou d'annulation)
            if full_reply:
                session.add_message(MessageRole.ASSISTANT, full_reply)
            
            await self.repository.save_session(session)
            logger.info(f"[Assistant] Session {session_id} saved (recovery={session.user_id != 'anonymous'})")
