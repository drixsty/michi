from typing import Optional
from loguru import logger
from modules.chat.domain.entities import ChatSession, MessageRole
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
        
        # 2. Boucle de raisonnement (Reasoning Loop)
        # On permet jusqu'à 3 tours d'outils pour éviter les boucles infinies
        for _ in range(3):
            response = await self.llm_provider.generate_response(session.messages)
            
            # Si c'est du texte simple, on a fini
            if isinstance(response, str):
                session.add_message(MessageRole.ASSISTANT, response)
                await self.repository.save_session(session)
                return response
            
            # Sinon, c'est un appel d'outil (Tool Call)
            for tool_call in response:
                func_name = tool_call.function.name
                logger.info(f"[Assistant] Executing tool: {func_name}")
                
                # Exécution réelle de l'outil
                result_data = "{}"
                if func_name == "get_inventory":
                    data = await self.michi_api.get_inventory_status(org_id, jwt)
                    result_data = str(data)
                elif func_name == "get_alerts":
                    data = await self.michi_api.get_forecasting_alerts(org_id, jwt)
                    result_data = str(data)
                
                # On ajoute le résultat au contexte (via un message système pour le moment)
                # Note: OpenAI préfère un rôle 'tool', mais on simplifie pour le domaine Michi
                session.add_message(MessageRole.SYSTEM, f"RÉSULTAT DE {func_name}: {result_data}")

        # Fallback si trop de tours
        await self.repository.save_session(session)
        return "J'ai récupéré beaucoup d'informations, mais je m'y perds un peu. Pouvez-vous préciser votre question ?"
