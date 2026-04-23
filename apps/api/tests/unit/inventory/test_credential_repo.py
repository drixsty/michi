import pytest
import uuid
from core.security.encryption import encryption_service
from modules.inventory.infrastructure.repositories.credential_repository import SQLAlchemyCredentialRepository
from modules.inventory.domain.entities import CredentialEntity
from modules.inventory.infrastructure.persistence.models import Store

@pytest.mark.asyncio
async def test_credential_repository_encryption(db_session):
    # 1. Créer un store parent (requis pour la FK)
    from core.database.models import Organization
    org = Organization(id=uuid.uuid4(), name="Test Org", slug="test-org")
    db_session.add(org)
    await db_session.commit()
    
    store = Store(
        id=uuid.uuid4(),
        organization_id=org.id,
        name="Test Store",
        platform="SHOPIFY"
    )
    db_session.add(store)
    await db_session.commit()

    repo = SQLAlchemyCredentialRepository(db_session)
    
    # 2. Sauvegarder des credentials
    entity = CredentialEntity(
        id=uuid.uuid4(),
        store_id=store.id,
        api_key="michi_123",
        access_token="token_456"
    )
    
    await repo.save(entity)
    await db_session.commit()
    
    # 3. Récupérer et vérifier le déchiffrement transparent
    retrieved = await repo.get_by_store(store.id)
    assert retrieved.api_key == "michi_123"
    assert retrieved.access_token == "token_456"
    
    # 4. Vérifier que c'est chiffré en DB (texte brut absent)
    from sqlalchemy import text
    result = await db_session.execute(text(f"SELECT encrypted_api_key FROM store_credentials WHERE store_id = '{store.id}'"))
    encrypted_val = result.scalar()
    assert "michi_123" not in encrypted_val
