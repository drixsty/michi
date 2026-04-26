from typing import Protocol, List, Dict, Any, Optional
from modules.chat.domain.entities import ChatMessage, AssistantAction

class ILLMProvider(Protocol):
    """Port de sortie pour le fournisseur de LLM (OpenAI, Anthropic, etc.)"""
    async def generate_response(
        self, 
        messages: List[ChatMessage], 
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto"
    ) -> Any: # Retourne soit str, soit un objet ToolCall
        ...

    async def classify_intent(self, user_input: str) -> str:
        ...

class IMichiApiPort(Protocol):
    """Port de sortie pour interagir avec l'API Michi principale"""
    async def get_inventory_status(self, org_id: str, jwt: str) -> Dict[str, Any]:
        ...

    async def get_forecasting_alerts(self, org_id: str, jwt: str) -> List[Dict[str, Any]]:
        ...

class IChatRepository(Protocol):
    """Port pour la persistance des sessions de chat"""
    async def save_session(self, session: Any) -> None:
        ...

    async def get_session(self, session_id: str) -> Optional[Any]:
        ...

    async def list_sessions(self, user_id: str, org_id: str) -> List[Any]:
        ...

    async def delete_session(self, session_id: str) -> bool:
        ...
