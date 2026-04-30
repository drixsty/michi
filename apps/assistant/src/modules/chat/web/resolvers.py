import strawberry
from typing import List, Optional, AsyncGenerator
from datetime import datetime

@strawberry.type
class ChatMessageGQL:
    id: Optional[str]
    role: str
    content: str
    timestamp: datetime
    rating: Optional[str] = None
    feedback_text: Optional[str] = None

@strawberry.type
class ChatSessionGQL:
    session_id: str
    updated_at: datetime
    title: Optional[str] = None
    last_message: Optional[str] = None
    messages: Optional[List[ChatMessageGQL]] = None

@strawberry.type
class AssistantResponse:
    reply: str
    session_id: str
    suggested_actions: Optional[List[str]] = None

async def get_auth_context(info: strawberry.types.Info) -> tuple[str, str, str]:
    """Extrait user_id, org_id et jwt_token du contexte (Request ou WebSocket)."""
    request = info.context.get("request")
    websocket = info.context.get("websocket")
    
    auth_header = None
    michi_org_id_header = None
    if request:
        auth_header = request.headers.get("Authorization")
        michi_org_id_header = request.headers.get("michi-org-id")
    elif websocket:
        headers = dict(websocket.scope.get("headers", []))
        # Support Authorization in headers (lowercase for dict from scope) or connection_params
        auth_header = headers.get(b"authorization", b"").decode() or \
                      websocket.scope.get("connection_params", {}).get("Authorization")
        michi_org_id_header = headers.get(b"michi-org-id", b"").decode()

    user_id = "anonymous"
    org_id = "anonymous"
    jwt_token = ""

    if auth_header and " " in auth_header:
        jwt_token = auth_header.split(" ")[1]
        try:
            from core.security.tokens import decode_access_token
            payload = decode_access_token(jwt_token)
            user_id = payload.get("user_id", "anonymous")
            org_id = payload.get("org_id")
            
            # Fallback sur le header si org_id absent du token
            if not org_id or org_id == "anonymous":
                org_id = michi_org_id_header

            org_id = org_id or "anonymous"
            from loguru import logger
            logger.debug(f"Auth Success: user={user_id}, org={org_id}")
        except Exception as e:
            from loguru import logger
            logger.warning(f"Auth Failure: {e}")
            
    return user_id, org_id, jwt_token

@strawberry.type
class ChatQuery:
    @strawberry.field
    def hello(self) -> str:
        return "Assistant Michi prêt."

    @strawberry.field
    async def list_sessions(self, info: strawberry.types.Info) -> List[ChatSessionGQL]:
        from core.di import container
        
        user_id, org_id, _ = await get_auth_context(info)
        
        from loguru import logger
        logger.debug(f"[Resolvers] list_sessions for user={user_id}, org={org_id}")
        
        if user_id == "anonymous":
            return []

        db = info.context.get("db")
        if not db:
            logger.error("[Resolvers] Database session missing in context!")
            return []

        repo = container.get_chat_repository(db)
        sessions = await repo.list_sessions(user_id, org_id)

        return [
            ChatSessionGQL(
                session_id=s.session_id,
                updated_at=s.updated_at,
                title=s.title,
                last_message=s.title or "Conversation Michi"
            ) for s in sessions
        ]

    @strawberry.field
    async def get_session(self, info: strawberry.types.Info, session_id: str) -> Optional[ChatSessionGQL]:
        if not session_id: return None
        
        user_id, _, _ = await get_auth_context(info)
        
        from core.di import container
        db = info.context.get("db")
        repo = container.get_chat_repository(db)
        try:
            session = await repo.get_session(session_id)
            if not session: return None
            
            return ChatSessionGQL(
                session_id=session.session_id,
                updated_at=session.updated_at,
                title=session.title,
                messages=[
                    ChatMessageGQL(
                        id=m.id,
                        role=m.role.value,
                        content=m.content,
                        timestamp=m.timestamp,
                        rating=m.rating,
                        feedback_text=m.feedback_text
                    ) for m in session.messages
                ]
            )
        except Exception as e:
            from loguru import logger
            logger.error(f"Error in get_session: {e}")
            return None

    @strawberry.field
    async def get_chat_history(self, info: strawberry.types.Info, session_id: str) -> List[ChatMessageGQL]:
        session = await self.get_session(info, session_id)
        return session.messages if session and session.messages else []

@strawberry.type
class ChatMutation:
    @strawberry.mutation
    async def delete_session(self, info: strawberry.types.Info, session_id: str) -> bool:
        from core.di import container
        db = info.context.get("db")
        repo = container.get_chat_repository(db)
        return await repo.delete_session(session_id)

    @strawberry.mutation
    async def update_session_title(self, info: strawberry.types.Info, session_id: str, title: str) -> bool:
        from core.di import container
        db = info.context.get("db")
        repo = container.get_chat_repository(db)
        return await repo.rename_session(session_id, title)

    @strawberry.mutation
    async def rate_message(
        self, 
        info: strawberry.types.Info, 
        message_id: str, 
        rating: str, 
        feedback_text: Optional[str] = None
    ) -> bool:
        from core.di import container
        db = info.context.get("db")
        repo = container.get_chat_repository(db)
        return await repo.rate_message(message_id, rating, feedback_text)

    @strawberry.mutation
    async def upload_file(
        self, 
        info: strawberry.types.Info, 
        file: strawberry.file_uploads.Upload,
        session_id: Optional[str] = None
    ) -> str:
        """Upload un fichier et retourne son contenu texte extrait."""
        import os
        content = await file.read()
        filename = file.filename
        extension = os.path.splitext(filename)[1].lower()
        
        extracted_text = f"[Contenu du fichier {filename}]:\n"
        if extension == ".csv":
            extracted_text += content.decode("utf-8")[:2000]
        else:
            extracted_text += "Fichier binaire non encore supporté en parsing complet."
            
        return extracted_text

    @strawberry.mutation
    async def send_message(
        self, 
        info: strawberry.types.Info,
        content: str, 
        session_id: Optional[str] = None
    ) -> AssistantResponse:
        from core.di import container
        import uuid

        user_id, org_id, jwt_token = await get_auth_context(info)

        db = info.context.get("db")
        use_case = container.get_process_message_use_case(db)
        actual_session_id = session_id or str(uuid.uuid4())
        
        reply = await use_case.execute(
            session_id=actual_session_id,
            user_id=user_id,
            org_id=org_id,
            content=content,
            jwt=jwt_token
        )

        return AssistantResponse(
            reply=reply,
            session_id=actual_session_id
        )

@strawberry.type
class Subscription:
    @strawberry.subscription
    async def assistant_response(
        self, 
        info: strawberry.types.Info,
        content: str, 
        session_id: Optional[str] = None
    ) -> AsyncGenerator[AssistantResponse, None]:
        from core.di import container
        import uuid

        user_id, org_id, jwt_token = await get_auth_context(info)

        db = info.context.get("db")
        use_case = container.get_process_message_use_case(db)
        actual_session_id = session_id or str(uuid.uuid4())
        
        async for chunk in use_case.execute_stream(
            session_id=actual_session_id,
            user_id=user_id,
            org_id=org_id,
            content=content,
            jwt=jwt_token
        ):
            yield AssistantResponse(
                reply=chunk,
                session_id=actual_session_id
            )
        
        yield AssistantResponse(
            reply="",
            session_id=actual_session_id,
            suggested_actions=["Analyser les coûts", "Voir les alternatives fournisseurs", "Simuler une rupture"]
        )

schema = strawberry.Schema(query=ChatQuery, mutation=ChatMutation, subscription=Subscription)
