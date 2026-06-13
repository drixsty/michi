from core.server import mcp
from core.api.client import MichiApiClient
from core.context import jwt_token_var, org_id_var
from core.security.tokens import generate_dev_jwt, get_dev_token_claims
from typing import Optional, List
from loguru import logger

client = MichiApiClient()

async def _get_auth_credentials() -> tuple[str, str]:
    """Retrieve jwt and org_id from contextvars, or fallback to dev credentials."""
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
            logger.debug("[MCP Tools] Missing authentication token. Generating development fallback token...")
            jwt = await generate_dev_jwt()
            claims = await get_dev_token_claims()
            org_id = claims["org_id"]
        
    return org_id, jwt

@mcp.tool()
async def get_inventory_status() -> str:
    """
    Get the current omnichannel inventory status, including total stock, days of stock, and risk values.
    
    Returns:
        A Markdown table displaying the status of each SKU.
    """
    try:
        org_id, jwt = await _get_auth_credentials()
        items = await client.get_omnichannel_inventory(org_id, jwt)
        
        if not items:
            return "No inventory items found."
            
        md = ["### Omnichannel Inventory Status\n"]
        md.append("| SKU | Title | Total Stock | Days of Stock | Risk Value |")
        md.append("|---|---|---|---|---|")
        for item in items:
            md.append(
                f"| {item.get('sku')} | {item.get('title')} | {item.get('totalStock')} | "
                f"{item.get('daysOfStock')} | {item.get('riskValue')} |"
            )
        return "\n".join(md)
    except Exception as e:
        logger.error(f"Error in get_inventory_status tool: {e}")
        return f"Error fetching inventory: {str(e)}"

@mcp.tool()
async def get_replenishment_alerts() -> str:
    """
    Retrieve predictions and active replenishment alerts, showing the predicted stockout date and recommended reorder date.
    
    Returns:
        A Markdown list of items requiring replenishment.
    """
    try:
        org_id, jwt = await _get_auth_credentials()
        items = await client.get_predictions(org_id, jwt)
        
        if not items:
            return "No active replenishment alerts or predictions found."
            
        md = ["### Replenishment Alerts & Predictions\n"]
        md.append("| SKU | Title | Run Rate | Stockout Date | Reorder Qty | Reorder Alert Date |")
        md.append("|---|---|---|---|---|---|")
        
        for item in items:
            stockout_date = item.get("predictedStockoutDate") or "Never"
            alert_date = item.get("reorderAlertDate") or "N/A"
            md.append(
                f"| {item.get('sku')} | {item.get('title')} | {item.get('runRate'):.2f}/day | "
                f"{stockout_date} | {item.get('replenishmentQuantity')} | {alert_date} |"
            )
        return "\n".join(md)
    except Exception as e:
        logger.error(f"Error in get_replenishment_alerts tool: {e}")
        return f"Error fetching replenishment alerts: {str(e)}"

@mcp.tool()
async def simulate_forecast(sku: str, safety_factor: float) -> str:
    """
    Simulate a forecasting scenario for a specific SKU, adjusting safety stock using a custom multiplier.
    
    Args:
        sku: The unique product SKU to simulate.
        safety_factor: Multiplier to apply to the safety stock calculation (e.g. 1.5 to increase safety margin).
    """
    try:
        org_id, jwt = await _get_auth_credentials()
        predictions = await client.get_predictions(org_id, jwt)
        
        target_item = None
        for item in predictions:
            if item.get("sku") == sku:
                target_item = item
                break
                
        if not target_item:
            return f"Product with SKU '{sku}' not found in predictions."
            
        run_rate = target_item.get("runRate") or 0.0
        reorder_qty = target_item.get("replenishmentQuantity") or 0
        
        # Simulated safety stock calculation
        simulated_qty = int(reorder_qty * safety_factor)
        
        md = [
            f"### Forecast Simulation for SKU: {sku}",
            f"* **Current Run Rate**: {run_rate:.2f} units/day",
            f"* **Base Reorder Quantity**: {reorder_qty} units",
            f"* **Safety Stock Multiplier**: {safety_factor}x",
            f"* **Simulated Reorder Quantity**: {simulated_qty} units",
            "\n*Note: Increasing the safety factor protects against supply chain volatility but increases inventory holding costs.*"
        ]
        return "\n".join(md)
    except Exception as e:
        logger.error(f"Error in simulate_forecast tool: {e}")
        return f"Error simulating forecast: {str(e)}"

@mcp.tool()
async def generate_purchase_order(product_id: str, supplier_id: str, quantity: int) -> str:
    """
    Create a supplier purchase order draft for a product.
    
    Args:
        product_id: The UUID of the product.
        supplier_id: The UUID of the supplier.
        quantity: The quantity to order.
    """
    try:
        org_id, jwt = await _get_auth_credentials()
        po = await client.create_purchase_order(org_id, jwt, product_id, supplier_id, quantity)
        
        if not po or "id" not in po:
            return "Failed to create purchase order. Check product/supplier IDs."
            
        return (
            f"### Purchase Order Draft Created Successfully!\n"
            f"* **PO ID**: {po.get('id')}\n"
            f"* **Quantity**: {po.get('quantity')}\n"
            f"* **Status**: {po.get('status')}\n"
            f"* **Created At**: {po.get('createdAt')}"
        )
    except Exception as e:
        logger.error(f"Error in generate_purchase_order tool: {e}")
        return f"Error creating purchase order: {str(e)}"

@mcp.tool()
async def trigger_data_sync(store_id: str) -> str:
    """
    Trigger the prediction pipeline run for a specific store.
    
    Args:
        store_id: The UUID of the store to synchronize.
    """
    try:
        org_id, jwt = await _get_auth_credentials()
        res = await client.run_prediction_pipeline(org_id, jwt, store_id)
        
        if res.get("success"):
            return (
                f"### Synchronization Triggered Successfully!\n"
                f"* **Message**: {res.get('message')}\n"
                f"* **Products Processed**: {res.get('productsProcessed')}"
            )
        else:
            return f"Failed to trigger synchronization: {res.get('message', 'Unknown error')}"
    except Exception as e:
        logger.error(f"Error in trigger_data_sync tool: {e}")
        return f"Error triggering sync: {str(e)}"
