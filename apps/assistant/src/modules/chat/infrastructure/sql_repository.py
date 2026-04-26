import uuid
from typing import Optional, Any, List
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from modules.chat.domain.entities import ChatSession, ChatMessage, MessageRole
from modules.chat.domain.ports import IChatRepository
from modules.chat.infrastructure.models import ChatSessionModel, ChatMessageModel

class SQLAlchemyChatRepository(IChatRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_session(self, session: ChatSession) -> None:
        # 1. Vérifier si la session existe
        stmt = select(ChatSessionModel).where(ChatSessionModel.id == session.session_id)
        result = await self.db.execute(stmt)
        db_session = result.scalar_one_or_none()

        if not db_session:
            db_session = ChatSessionModel(
                id=session.session_id,
                user_id=session.user_id,
                org_id=session.org_id,
                metadata_json=session.metadata
            )
            self.db.add(db_session)

        # 2. Synchroniser les messages (Approche simple : on ajoute les nouveaux)
        # On compare par timestamp ou on vide et on recrée pour le MVP
        # Ici on va juste ajouter les messages qui n'ont pas d'ID (si on en avait)
        # Mais le domaine ne porte pas les IDs des messages.
        # Solution robuste : on vide les messages et on les recrée tous pour préserver l'ordre
        from sqlalchemy import delete
        await self.db.execute(delete(ChatMessageModel).where(ChatMessageModel.session_id == session.session_id))
        
        for msg in session.messages:
            db_msg = ChatMessageModel(
                id=str(uuid.uuid4()),
                session_id=session.session_id,
                role=msg.role.value,
                content=msg.content,
                timestamp=msg.timestamp
            )
            self.db.add(db_msg)
        
        await self.db.commit()

    async def get_session(self, session_id: str) -> Optional[ChatSession]:
        stmt = select(ChatSessionModel).where(ChatSessionModel.id == session_id).options(selectinload(ChatSessionModel.messages))
        result = await self.db.execute(stmt)
        db_session = result.scalar_one_or_none()

        if not db_session:
            return None

        messages = [
            ChatMessage(
                role=MessageRole(msg.role),
                content=msg.content,
                timestamp=msg.timestamp
            ) for msg in sorted(db_session.messages, key=lambda x: x.timestamp)
        ]

        return ChatSession(
            session_id=db_session.id,
            user_id=db_session.user_id,
            org_id=db_session.org_id,
            messages=messages,
            metadata=db_session.metadata_json or {}
        )

    async def list_sessions(self, user_id: str, org_id: str) -> List[ChatSession]:
        stmt = select(ChatSessionModel).where(
            ChatSessionModel.user_id == user_id,
            ChatSessionModel.org_id == org_id
        ).order_by(ChatSessionModel.updated_at.desc())
        
        result = await self.db.execute(stmt)
        db_sessions = result.scalars().all()

        return [
            ChatSession(
                session_id=s.id,
                user_id=s.user_id,
                org_id=s.org_id,
                messages=[], # On ne charge pas les messages pour la liste
                metadata=s.metadata_json or {}
            ) for s in db_sessions
        ]

    async def delete_session(self, session_id: str) -> bool:
        from sqlalchemy import delete
        try:
            # Les messages devraient être supprimés en cascade si configuré, 
            # sinon on le fait manuellement
            await self.db.execute(delete(ChatMessageModel).where(ChatMessageModel.session_id == session_id))
            await self.db.execute(delete(ChatSessionModel).where(ChatSessionModel.id == session_id))
            await self.db.commit()
            return True
        except Exception as e:
            print(f"Error deleting session: {e}")
            await self.db.rollback()
            return False

    async def truncate_session(self, session_id: str, message_index: int) -> bool:
        """Supprime tous les messages à partir d'un certain index pour permettre l'édition"""
        from sqlalchemy import delete
        stmt = select(ChatMessageModel).where(ChatMessageModel.session_id == session_id).order_by(ChatMessageModel.timestamp.asc())
        result = await self.db.execute(stmt)
        messages = result.scalars().all()
        
        if message_index < len(messages):
            to_delete = [m.id for m in messages[message_index:]]
            await self.db.execute(delete(ChatMessageModel).where(ChatMessageModel.id.in_(to_delete)))
            await self.db.commit()
            return True
        return False
