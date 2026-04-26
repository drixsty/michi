import strawberry
from typing import List, Optional
from datetime import datetime

@strawberry.type
class ChatMessageGQL:
    role: str
    content: str
    timestamp: datetime

@strawberry.type
class ChatSessionGQL:
    session_id: str
    updated_at: datetime
    last_message: Optional[str] = None

@strawberry.type
class AssistantResponse:
    reply: str
    session_id: str
    suggested_actions: Optional[List[str]] = None

@strawberry.type
class ChatQuery:
    @strawberry.field
    def hello(self) -> str:
        return "Assistant Michi prêt."

    @strawberry.field
    async def list_sessions(self, info: strawberry.types.Info) -> List[ChatSessionGQL]:
        from core.di import container
        from core.security.tokens import decode_access_token
        
        request = info.context.get("request")
        auth_header = request.headers.get("Authorization")
        if not auth_header: return []

        payload = decode_access_token(auth_header.split(" ")[1])
        user_id = payload.get("sub")
        org_id = payload.get("org_id")

        db = info.context.get("db")
        repo = container.get_chat_repository(db)
        sessions = await repo.list_sessions(user_id, org_id)

        return [
            ChatSessionGQL(
                session_id=s.session_id,
                updated_at=datetime.utcnow(), # Placeholder car non porté par le domaine pur
                last_message="Conversation Michi"
            ) for s in sessions
        ]

    @strawberry.field
    async def get_chat_history(self, info: strawberry.types.Info, session_id: str) -> List[ChatMessageGQL]:
        from core.di import container
        db = info.context.get("db")
        repo = container.get_chat_repository(db)
        session = await repo.get_session(session_id)
        if not session: return []
        
        return [
            ChatMessageGQL(
                role=m.role.value,
                content=m.content,
                timestamp=m.timestamp
            ) for m in session.messages
        ]

@strawberry.type
class ChatMutation:
    @strawberry.mutation
    async def delete_session(self, info: strawberry.types.Info, session_id: str) -> bool:
        from core.di import container
        db = info.context.get("db")
        repo = container.get_chat_repository(db)
        return await repo.delete_session(session_id)

    @strawberry.mutation
    async def truncate_session(self, info: strawberry.types.Info, session_id: str, index: int) -> bool:
        from core.di import container
        db = info.context.get("db")
        repo = container.get_chat_repository(db)
        return await repo.truncate_session(session_id, index)

    @strawberry.mutation
    async def send_message(
        self, 
        info: strawberry.types.Info,
        content: str, 
        session_id: Optional[str] = None
    ) -> AssistantResponse:
        from core.di import container
        from core.security.tokens import decode_access_token
        import uuid

        # 1. Extraction et validation du JWT
        request = info.context.get("request")
        auth_header = request.headers.get("Authorization")
        
        user_id = "anonymous"
        org_id = "anonymous"
        jwt_token = ""

        if auth_header and auth_header.startswith("Bearer "):
            jwt_token = auth_header.split(" ")[1]
            try:
                payload = decode_access_token(jwt_token)
                user_id = payload.get("sub", "anonymous")
                org_id = payload.get("org_id", "anonymous")
            except Exception:
                pass

        # 2. Récupération du Use Case via le Container (avec session DB)
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
            session_id=actual_session_id,
            suggested_actions=["Voir mon stock", "Analyser les risques"]
        )

schema = strawberry.Schema(query=ChatQuery, mutation=ChatMutation)
