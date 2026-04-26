from openai import AsyncOpenAI
from typing import List, Dict, Any, Optional
from loguru import logger
from modules.chat.domain.entities import ChatMessage, MessageRole
from modules.chat.domain.ports import ILLMProvider
from core.config.settings import settings

class OpenAIProvider(ILLMProvider):
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o" # Ou "gpt-3.5-turbo" selon le budget/besoin

    async def generate_response(
        self, 
        messages: List[ChatMessage], 
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto"
    ) -> Any:
        """Génère une réponse intelligente avec support des outils."""
        
        system_prompt = {
            "role": "system",
            "content": (
                "Tu es Michi Assistant (道), expert supply chain. "
                "Tu as accès à des outils pour consulter l'inventaire et les alertes. "
                "Utilise-les si l'utilisateur pose une question spécifique sur ses données."
            )
        }

        openai_messages = [system_prompt]
        for msg in messages:
            openai_messages.append({"role": msg.role.value, "content": msg.content})

        # Définition par défaut des outils Michi si non fournis
        michi_tools = tools or [
            {
                "type": "function",
                "function": {
                    "name": "get_inventory",
                    "description": "Récupère l'état global des stocks et les risques",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_alerts",
                    "description": "Récupère les alertes de prévision et de rupture",
                    "parameters": {"type": "object", "properties": {}}
                }
            }
        ]

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                tools=michi_tools,
                tool_choice=tool_choice,
                temperature=0.7
            )
            
            message = response.choices[0].message
            
            # Si l'IA veut appeler un outil
            if message.tool_calls:
                return message.tool_calls
            
            return message.content
        except Exception as e:
            logger.error(f"[OpenAIProvider] Error: {str(e)}")
            return "Désolé, je rencontre une erreur technique."

    async def classify_intent(self, user_input: str) -> str:
        """
        Analyse l'intention brute pour aider l'orchestrateur.
        Note: Dans une version plus avancée, on utiliserait le Tool Calling.
        """
        # Utilisation d'un mini-prompt pour la classification
        prompt = f"Analyse l'intention de cette phrase de l'utilisateur : '{user_input}'. Répond uniquement par un des mots suivants : QUERY_INVENTORY, QUERY_ALERTS, GENERAL_CHAT."
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini", # Plus rapide et moins cher pour la classification
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return "GENERAL_CHAT"
