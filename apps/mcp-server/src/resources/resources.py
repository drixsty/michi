from core.server import mcp
from core.api.client import MichiApiClient
from core.context import jwt_token_var, org_id_var
from core.security.tokens import generate_dev_jwt, get_dev_token_claims
from loguru import logger
import json

client = MichiApiClient()

async def _get_auth_credentials() -> tuple[str, str]:
    """Retrieve credentials or fallback to dev ones."""
    jwt = jwt_token_var.get()
    org_id = org_id_var.get()
    
    if settings.ENVIRONMENT == "production":
        if not jwt or not org_id:
            raise ValueError("Unauthenticated: Missing JWT token or Organization ID in request headers/query.")
        
        # Verify JWT signature and claims
        from core.security.tokens import decode_access_token
        try:
            claims = decode_access_token(jwt)
            token_org_id = claims.get("org_id")
            if token_org_id and token_org_id != org_id:
                raise ValueError("Unauthorized: Organization ID mismatch in token claims.")
        except Exception as e:
            raise ValueError(f"Unauthenticated: Invalid or expired JWT token: {str(e)}")
            
    else:
        # Development fallback
        if not jwt or not org_id:
            logger.debug("[MCP Resources] Missing auth token. Using development fallback...")
            jwt = await generate_dev_jwt()
            claims = await get_dev_token_claims()
            org_id = claims["org_id"]
        
    return org_id, jwt

@mcp.resource("michi://products/{sku}")
async def get_product_resource(sku: str) -> str:
    """
    Fetch structured forecasting and inventory information about a specific SKU.
    """
    try:
        org_id, jwt = await _get_auth_credentials()
        predictions = await client.get_predictions(org_id, jwt)
        
        for item in predictions:
            if item.get("sku") == sku:
                return json.dumps(item, indent=2, ensure_ascii=False)
                
        return json.dumps({"error": f"Product with SKU '{sku}' not found."}, indent=2)
    except Exception as e:
        logger.error(f"Error in get_product_resource: {e}")
        return json.dumps({"error": str(e)}, indent=2)

@mcp.resource("michi://alerts/active")
async def get_alerts_resource() -> str:
    """
    Fetch all active replenishment alerts and predictions.
    """
    try:
        org_id, jwt = await _get_auth_credentials()
        predictions = await client.get_predictions(org_id, jwt)
        return json.dumps(predictions, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error in get_alerts_resource: {e}")
        return json.dumps({"error": str(e)}, indent=2)

@mcp.resource("michi://suppliers")
async def get_suppliers_resource() -> str:
    """
    Fetch the list of suppliers.
    """
    try:
        org_id, jwt = await _get_auth_credentials()
        suppliers = await client.get_suppliers(org_id, jwt)
        return json.dumps(suppliers, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error in get_suppliers_resource: {e}")
        return json.dumps({"error": str(e)}, indent=2)

@mcp.resource("michi://forecasting/kpis")
async def get_kpis_resource() -> str:
    """
    Fetch global inventory and stockout KPIs.
    """
    try:
        org_id, jwt = await _get_auth_credentials()
        kpis = await client.get_dashboard_kpis(org_id, jwt)
        return json.dumps(kpis, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error in get_kpis_resource: {e}")
        return json.dumps({"error": str(e)}, indent=2)
