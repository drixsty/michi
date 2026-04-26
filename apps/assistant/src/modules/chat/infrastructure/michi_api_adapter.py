import httpx
from typing import List, Dict, Any, Optional
from loguru import logger
from modules.chat.domain.ports import IMichiApiPort
from core.config.settings import settings

class MichiApiAdapter(IMichiApiPort):
    def __init__(self):
        self.url = settings.MICHI_API_URL

    async def get_inventory_status(self, org_id: str, jwt: str) -> Dict[str, Any]:
        """Récupère l'inventaire omnichannel via GraphQL"""
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
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.url,
                    json={"query": query},
                    headers={"Authorization": f"Bearer {jwt}", "michi-org-id": org_id}
                )
                response.raise_for_status()
                data = response.json()
                
                if "errors" in data:
                    logger.error(f"[MichiApiAdapter] GraphQL errors: {data['errors']}")
                    return {"error": "GraphQL Error"}
                
                return data["data"]["omnichannelInventory"]
        except Exception as e:
            logger.error(f"[MichiApiAdapter] Connection error: {str(e)}")
            return {"error": str(e)}

    async def get_forecasting_alerts(self, org_id: str, jwt: str) -> List[Dict[str, Any]]:
        """Récupère les alertes non lues"""
        query = """
        query GetUnreadAlerts {
            unreadAlerts {
                id
                sku
                type
                message
                severity
            }
        }
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.url,
                    json={"query": query},
                    headers={"Authorization": f"Bearer {jwt}", "michi-org-id": org_id}
                )
                response.raise_for_status()
                data = response.json()
                return data["data"]["unreadAlerts"]
        except Exception as e:
            logger.error(f"[MichiApiAdapter] Connection error: {str(e)}")
            return []
