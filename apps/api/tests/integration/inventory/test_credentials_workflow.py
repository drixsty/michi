import pytest
import uuid
from core.security.encryption import encryption_service
from modules.inventory.infrastructure.persistence.models import Store, StoreCredential
from core.security.plans import PlanName
from sqlalchemy import select

@pytest.mark.asyncio
async def test_update_credentials_e2e(client, auth_headers, db_session):
    # 1. Créer un store de test pour l'org de l'utilisateur
    # Note: On suppose que l'utilisateur de test a déjà une org via les fixtures
    from core.database.models import Organization
    stmt = select(Organization).limit(1)
    result = await db_session.execute(stmt)
    org = result.scalar()
    
    # Passer l'org en plan PRO pour que la mutation soit acceptée
    org.plan = "PRO"
    await db_session.commit()

    store = Store(
        id=uuid.uuid4(),
        organization_id=org.id,
        name="Test Store",
        platform="SHOPIFY",
        connected=True
    )
    db_session.add(store)
    await db_session.commit()

    # 2. Mutation GraphQL
    mutation = """
        mutation UpdateCreds($input: UpdateCredentialInput!) {
            updateStoreCredentials(input: $input) {
                id
                apiKeyLastChars
                hasToken
                meta
            }
        }
    """
    
    variables = {
        "input": {
            "storeId": str(store.id),
            "apiKey": "michi_secret_key_9999",
            "accessToken": "shpat_abc123",
            "metaJson": '{"shop": "test.myshopify.com"}'
        }
    }
    
    response = await client.post("/graphql", json={"query": mutation, "variables": variables}, headers=auth_headers)
    data = response.json()
    
    # 3. Vérifications
    assert "errors" not in data
    res = data["data"]["updateStoreCredentials"]
    assert res["apiKeyLastChars"] == "9999"
    assert res["hasToken"] is True
    
    # 4. Vérification du chiffrement en base de données
    # On vide le cache de session pour forcer une relecture DB
    store_id = store.id
    db_session.expire_all()
    stmt = select(StoreCredential).where(StoreCredential.store_id == store_id)
    result = await db_session.execute(stmt)
    db_cred = result.scalar()
    
    assert db_cred.encrypted_api_key is not None
    assert "michi_secret_key_9999" not in db_cred.encrypted_api_key
    
    # Vérifier qu'on peut déchiffrer manuellement
    decrypted = encryption_service.decrypt(db_cred.encrypted_api_key)
    assert decrypted == "michi_secret_key_9999"
