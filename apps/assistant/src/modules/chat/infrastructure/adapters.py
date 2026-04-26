from typing import List, Dict, Any, Optional
from modules.chat.domain.entities import ChatMessage
from modules.chat.domain.ports import ILLMProvider, IMichiApiPort, IChatRepository

class MockLLMProvider(ILLMProvider):
    async def generate_response(self, messages: List[ChatMessage], tools=None) -> str:
        last_msg = messages[-1].content.lower()
        if "stock" in last_msg or "inventaire" in last_msg:
            return "D'après mes analyses, votre stock est sain, mais le SKU-123 arrive à son point de commande."
        return "Je suis Michi Assistant. Comment puis-je vous aider dans votre gestion de stock aujourd'hui ?"

    async def classify_intent(self, user_input: str) -> str:
        if "stock" in user_input.lower() or "inventaire" in user_input.lower():
            return "QUERY_INVENTORY"
        return "GENERAL_CHAT"

class MockMichiApiAdapter(IMichiApiPort):
    async def get_inventory_status(self, org_id: str, jwt: str) -> Dict[str, Any]:
        return {"total_items": 150, "stockouts": 2, "at_risk": 5}

    async def get_forecasting_alerts(self, org_id: str, jwt: str) -> List[Dict[str, Any]]:
        return [{"sku": "SKU-123", "type": "STOCKOUT_RISK"}]

class MemoryChatRepository(IChatRepository):
    def __init__(self):
        self._sessions = {}

    async def save_session(self, session: Any) -> None:
        self._sessions[session.session_id] = session

    async def get_session(self, session_id: str) -> Optional[Any]:
        return self._sessions.get(session_id)

# Singleton pour le développement
chat_repository = MemoryChatRepository()
