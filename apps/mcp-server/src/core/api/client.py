import httpx
from typing import List, Dict, Any, Optional
from loguru import logger
from core.config.settings import settings

class MichiApiClient:
    """GraphQL API Client to interface with the main Michi backend."""
    
    def __init__(self):
        self.url = settings.MICHI_API_URL

    async def _execute_query(
        self, 
        query: str, 
        variables: Optional[Dict[str, Any]] = None, 
        org_id: Optional[str] = None, 
        jwt: Optional[str] = None
    ) -> Dict[str, Any]:
        headers = {}
        if jwt:
            headers["Authorization"] = f"Bearer {jwt}"
        if org_id:
            headers["michi-org-id"] = org_id
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.url,
                    json={"query": query, "variables": variables or {}},
                    headers=headers,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                if "errors" in data:
                    logger.error(f"[MichiApiClient] GraphQL errors: {data['errors']}")
                    return {"errors": data["errors"]}
                
                return data.get("data", {})
        except Exception as e:
            logger.error(f"[MichiApiClient] Connection/GraphQL error: {str(e)}")
            return {"errors": [{"message": str(e)}]}

    async def get_omnichannel_inventory(self, org_id: str, jwt: str) -> List[Dict[str, Any]]:
        query = """
        query GetOmnichannelInventory {
            omnichannelInventory {
                sku
                title
                totalStock
                daysOfStock
                riskValue
            }
        }
        """
        res = await self._execute_query(query, org_id=org_id, jwt=jwt)
        if "errors" in res:
            return []
        return res.get("omnichannelInventory", [])

    async def get_predictions(self, org_id: str, jwt: str, store_id: Optional[str] = None) -> List[Dict[str, Any]]:
        query = """
        query GetPredictions($storeId: ID) {
            predictions(storeId: $storeId) {
                productId
                sku
                title
                runRate
                predictedStockoutDate
                replenishmentQuantity
                reorderAlertDate
            }
        }
        """
        variables = {"storeId": store_id} if store_id else {}
        res = await self._execute_query(query, variables=variables, org_id=org_id, jwt=jwt)
        if "errors" in res:
            return []
        return res.get("predictions", [])

    async def get_dashboard_kpis(self, org_id: str, jwt: str, store_id: Optional[str] = None) -> Dict[str, Any]:
        query = """
        query GetDashboardKPIs($storeId: ID) {
            dashboardKpis(storeId: $storeId) {
                totalProducts
                actualStockouts
                urgentAlerts
                predictedStockouts30d
                message
            }
        }
        """
        variables = {"storeId": store_id} if store_id else {}
        res = await self._execute_query(query, variables=variables, org_id=org_id, jwt=jwt)
        if "errors" in res:
            return {}
        return res.get("dashboardKpis", {})

    async def get_suppliers(self, org_id: str, jwt: str) -> List[Dict[str, Any]]:
        query = """
        query GetSuppliers {
            suppliers {
                id
                name
                leadTime
                moq
            }
        }
        """
        res = await self._execute_query(query, org_id=org_id, jwt=jwt)
        if "errors" in res:
            return []
        return res.get("suppliers", [])

    async def create_purchase_order(
        self, 
        org_id: str, 
        jwt: str, 
        product_id: str, 
        supplier_id: str, 
        quantity: int
    ) -> Dict[str, Any]:
        query = """
        mutation CreatePurchaseOrder($productId: ID!, $supplierId: ID!, $quantity: Int!) {
            createPurchaseOrder(productId: $productId, supplierId: $supplierId, quantity: $quantity) {
                id
                quantity
                status
                createdAt
            }
        }
        """
        variables = {
            "productId": product_id,
            "supplierId": supplier_id,
            "quantity": quantity
        }
        res = await self._execute_query(query, variables=variables, org_id=org_id, jwt=jwt)
        return res.get("createPurchaseOrder", {})

    async def run_prediction_pipeline(self, org_id: str, jwt: str, store_id: str) -> Dict[str, Any]:
        query = """
        mutation RunPredictionPipeline($storeId: ID!) {
            runPredictionPipeline(storeId: $storeId) {
                success
                productsProcessed
                message
            }
        }
        """
        variables = {"storeId": store_id}
        res = await self._execute_query(query, variables=variables, org_id=org_id, jwt=jwt)
        return res.get("runPredictionPipeline", {})
