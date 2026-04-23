from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.inventory.domain.entities import CredentialEntity
from modules.inventory.infrastructure.persistence.models import StoreCredential
from core.security.encryption import encryption_service

class SQLAlchemyCredentialRepository:
    """
    Repository pour les credentials avec chiffrement transparent.
    """
    def __init__(self, session: AsyncSession, encryptor=None):
        self.session = session
        self._encryptor = encryptor

    @property
    def encryption_service(self):
        if self._encryptor:
            return self._encryptor
        from core.security.encryption import encryption_service
        return encryption_service

    def _to_entity(self, model: StoreCredential) -> CredentialEntity:
        return CredentialEntity(
            id=model.id,
            store_id=model.store_id,
            access_token=self.encryption_service.decrypt(model.encrypted_access_token) if model.encrypted_access_token else None,
            api_key=self.encryption_service.decrypt(model.encrypted_api_key) if model.encrypted_api_key else None,
            api_secret=self.encryption_service.decrypt(model.encrypted_api_secret) if model.encrypted_api_secret else None,
            meta=model.meta,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    async def get_by_store(self, store_id: UUID) -> Optional[CredentialEntity]:
        stmt = select(StoreCredential).where(StoreCredential.store_id == store_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def save(self, entity: CredentialEntity) -> CredentialEntity:
        stmt = select(StoreCredential).where(StoreCredential.store_id == entity.store_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        # Chiffrement des données avant stockage
        encrypted_token = self.encryption_service.encrypt(entity.access_token) if entity.access_token else None
        encrypted_key = self.encryption_service.encrypt(entity.api_key) if entity.api_key else None
        encrypted_secret = self.encryption_service.encrypt(entity.api_secret) if entity.api_secret else None

        if model:
            model.encrypted_access_token = encrypted_token
            model.encrypted_api_key = encrypted_key
            model.encrypted_api_secret = encrypted_secret
            model.meta = entity.meta
        else:
            model = StoreCredential(
                id=entity.id,
                store_id=entity.store_id,
                encrypted_access_token=encrypted_token,
                encrypted_api_key=encrypted_key,
                encrypted_api_secret=encrypted_secret,
                meta=entity.meta
            )
            self.session.add(model)
        
        await self.session.flush()
        return self._to_entity(model)
