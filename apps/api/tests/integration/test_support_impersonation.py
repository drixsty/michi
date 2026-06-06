import pytest
import uuid
from sqlalchemy import select
from core.database.models import User, Organization, OrganizationMember, SupportAuditLog, Product
from core.database.constants import UserRole
from core.security import create_access_token
from core.security.hashing import hash_password

@pytest.mark.asyncio
@pytest.mark.integration
async def test_support_impersonation_and_audit_logging(client, db_session) -> None:
    # 1. Créer Org A (Support Org) et un utilisateur support
    org_support = Organization(
        id=uuid.uuid4(),
        name="Michi Support",
        slug="michi-support",
        plan="ENTERPRISE"
    )
    db_session.add(org_support)

    support_user = User(
        id=uuid.uuid4(),
        email="support@michi.com",
        hashed_password=hash_password("password123"),
        is_active=True,
        current_organization_id=org_support.id
    )
    db_session.add(support_user)
    await db_session.flush()

    # Assigner le rôle SUPPORT à l'agent
    support_member = OrganizationMember(
        organization_id=org_support.id,
        user_id=support_user.id,
        role=UserRole.SUPPORT
    )
    db_session.add(support_member)

    # 2. Créer Org B (Client Org) avec un produit
    org_client = Organization(
        id=uuid.uuid4(),
        name="Client Store",
        slug="client-store",
        plan="PRO"
    )
    db_session.add(org_client)

    # Créer un store pour associer les produits
    from modules.inventory.infrastructure.persistence.models import Store
    from modules.inventory.domain.entities import PlatformSource
    client_store_model = Store(
        id=uuid.uuid4(),
        name="Shopify Client",
        platform=PlatformSource.SHOPIFY,
        connected=True,
        organization_id=org_client.id
    )
    db_session.add(client_store_model)
    await db_session.flush()

    client_product = Product(
        id=uuid.uuid4(),
        title="Gobelet Michi",
        sku="GOB-MICH-001",
        lead_time=7,
        moq=10,
        current_stock=100,
        boost_factor=1.0,
        stock_weight=1.0,
        store_id=client_store_model.id
    )
    db_session.add(client_product)
    await db_session.flush()

    # Créer un utilisateur client normal
    client_user = User(
        id=uuid.uuid4(),
        email="client@store.com",
        hashed_password=hash_password("password123"),
        is_active=True,
        current_organization_id=org_client.id
    )
    db_session.add(client_user)
    await db_session.flush()

    client_member = OrganizationMember(
        organization_id=org_client.id,
        user_id=client_user.id,
        role=UserRole.ADMIN
    )
    db_session.add(client_member)
    await db_session.commit()

    # 3. Test 1 : L'utilisateur normal tente d'accéder à l'org support (IDOR) -> Doit échouer
    client_token = create_access_token({
        "user_id": str(client_user.id),
        "org_id": str(org_client.id),
        "email": client_user.email
    })

    query = """
        query {
            products {
                id
                title
            }
        }
    """

    response = await client.post(
        "/graphql",
        json={"query": query},
        headers={
            "Authorization": f"Bearer {client_token}",
            "michi-org-id": str(org_support.id)  # Essai IDOR vers Org Support
        }
    )
    
    assert response.status_code == 200
    res_data = response.json()
    assert "errors" in res_data
    assert any(err["extensions"].get("code") == "UNAUTHENTICATED" for err in res_data["errors"])

    # 4. Test 2 : L'agent support interroge l'org client (Impersonation) -> Doit réussir
    support_token = create_access_token({
        "user_id": str(support_user.id),
        "org_id": str(org_support.id),
        "email": support_user.email
    })

    response_support = await client.post(
        "/graphql",
        json={"query": query},
        headers={
            "Authorization": f"Bearer {support_token}",
            "michi-org-id": str(org_client.id)  # Tente d'impersonner Org Client
        }
    )

    assert response_support.status_code == 200
    res_support_data = response_support.json()
    assert "errors" not in res_support_data
    assert "data" in res_support_data
    assert len(res_support_data["data"]["products"]) == 1
    assert res_support_data["data"]["products"][0]["title"] == "Gobelet Michi"

    # 5. Test 3 : Vérifier qu'une ligne de log d'audit a été générée dans la DB
    stmt = select(SupportAuditLog).where(SupportAuditLog.support_user_id == support_user.id)
    audit_res = await db_session.execute(stmt)
    audit_logs = audit_res.scalars().all()

    assert len(audit_logs) == 1
    log = audit_logs[0]
    assert log.impersonated_org_id == org_client.id
    assert log.action == "graphql:products"
    assert log.flow_id is not None

    # 6. Test 4 : Vérifier l'accès aux requêtes de support (supportOrganizations, supportAuditLogs)
    # L'utilisateur normal ne doit PAS y avoir accès (FORBIDDEN)
    query_support_orgs = """
        query {
            supportOrganizations {
                id
                name
            }
        }
    """
    
    response_unauth_support = await client.post(
        "/graphql",
        json={"query": query_support_orgs},
        headers={
            "Authorization": f"Bearer {client_token}"
        }
    )
    assert response_unauth_support.status_code == 200
    res_unauth = response_unauth_support.json()
    assert "errors" in res_unauth
    assert any(err["extensions"].get("code") == "FORBIDDEN" for err in res_unauth["errors"])

    # L'agent support DOIT y avoir accès
    response_auth_support = await client.post(
        "/graphql",
        json={"query": query_support_orgs},
        headers={
            "Authorization": f"Bearer {support_token}"
        }
    )
    assert response_auth_support.status_code == 200
    res_auth = response_auth_support.json()
    assert "errors" not in res_auth
    assert "data" in res_auth
    assert len(res_auth["data"]["supportOrganizations"]) >= 2

    # Tester supportAuditLogs
    query_support_logs = """
        query {
            supportAuditLogs {
                id
                supportUserEmail
                impersonatedOrgName
                action
                flowId
            }
        }
    """
    response_auth_logs = await client.post(
        "/graphql",
        json={"query": query_support_logs},
        headers={
            "Authorization": f"Bearer {support_token}"
        }
    )
    assert response_auth_logs.status_code == 200
    res_logs = response_auth_logs.json()
    assert "errors" not in res_logs
    assert "data" in res_logs
    assert len(res_logs["data"]["supportAuditLogs"]) >= 1
    log_entry = next(l for l in res_logs["data"]["supportAuditLogs"] if l["action"] == "graphql:products")
    assert log_entry["supportUserEmail"] == "support@michi.com"
    assert log_entry["impersonatedOrgName"] == "Client Store"
    assert log_entry["flowId"] is not None
