"""
Tests d'intégration GraphQL
"""
import pytest


@pytest.mark.asyncio
@pytest.mark.integration
async def test_login_mutation(client):
    """Test mutation login via GraphQL"""
    query = """
        mutation Login($input: LoginInput!) {
            login(input: $input) {
                token
                user {
                    email
                }
            }
        }
    """
    
    # Créer d'abord un user (normalement fait par fixture)
    # Pour ce test, on suppose que seed_dev_data.py a été exécuté
    
    response = await client.post(
        "/graphql",
        json={
            "query": query,
            "variables": {
                "input": {
                    "email": "dev@michi.com",
                    "password": "password123"
                }
            }
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Vérifier structure réponse
    assert "data" in data
    assert "login" in data["data"]
    assert "token" in data["data"]["login"]
    assert data["data"]["login"]["user"]["email"] == "dev@michi.com"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_me_query_without_auth(client):
    """Test query me sans authentification"""
    query = """
        query {
            me {
                email
            }
        }
    """
    
    response = await client.post(
        "/graphql",
        json={"query": query}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Doit retourner une erreur UNAUTHENTICATED
    assert "errors" in data
    assert any("UNAUTHENTICATED" in str(error) for error in data["errors"])


@pytest.mark.asyncio
@pytest.mark.integration
async def test_me_query_with_auth(client, auth_token):
    """Test query me avec authentification"""
    query = """
        query {
            me {
                email
                shopId
            }
        }
    """
    
    response = await client.post(
        "/graphql",
        json={"query": query},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "data" in data
    assert "me" in data["data"]
    assert data["data"]["me"]["email"] == "test@michi.com"


@pytest.mark.asyncio
async def test_health_endpoint(client):
    """Test health check endpoint"""
    response = await client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "ok"
    assert "version" in data
