import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

@pytest.fixture
def client():
    from fastapi import FastAPI
    from core.server import mcp
    from main import AuthContextMiddleware
    
    app = FastAPI()
    app.add_middleware(AuthContextMiddleware)
    app.mount("/mcp", mcp.sse_app())
    
    @app.get("/health")
    async def health():
        return {"status": "ok"}
        
    return TestClient(app)

def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_sse_endpoint_validation_fails_with_invalid_host(client):
    # Verify that the SSE endpoint has DNS rebinding protection active
    # and correctly rejects requests with invalid Host headers
    with pytest.raises(ValueError, match="Request validation failed"):
        client.get("/mcp/sse", headers={"Host": "invalid-host.com"})


