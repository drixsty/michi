import pytest
from httpx import AsyncClient

async def test_prometheus_metrics_endpoint(client: AsyncClient):
    # 1. Effectue une requête normale pour générer des métriques
    response = await client.get("/")
    assert response.status_code == 200
    
    # 2. Récupère l'endpoint des métriques
    metrics_response = await client.get("/metrics")
    assert metrics_response.status_code == 200
    assert "text/plain" in metrics_response.headers["content-type"]
    
    content = metrics_response.text
    # 3. Vérifie que les métriques personnalisées HTTP sont bien enregistrées
    assert "http_requests_total" in content
    assert "http_request_duration_seconds" in content
