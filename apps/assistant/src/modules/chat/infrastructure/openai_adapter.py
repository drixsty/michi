from openai import AsyncOpenAI
from typing import List, Dict, Any, Optional
from loguru import logger
from modules.chat.domain.entities import ChatMessage, MessageRole
from modules.chat.domain.ports import ILLMProvider
from core.config.settings import settings

class OpenAIProvider(ILLMProvider):
    def __init__(self):
        logger.info("[OpenAIProvider] Initializing GPT-4o")
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o"
        self.system_prompt = (
            "Tu es Michi Assistant (道), expert supply chain. "
            "Tu as accès à des outils pour consulter l'inventaire et les alertes. "
            "Utilise-les si l'utilisateur pose une question spécifique sur ses données. "
            "Si tu as des données numériques à présenter, tu peux générer un graphique en utilisant un bloc de code markdown avec la langue 'chart' et un JSON respectant ce format : "
            "```chart\n"
            "{\n"
            "  \"type\": \"bar\" | \"line\",\n"
            "  \"title\": \"Titre du graphique\",\n"
            "  \"data\": [{ \"name\": \"Label\", \"value\": 10 }]\n"
            "}\n"
            "```"
        )

    async def generate_response(
        self, 
        messages: List[ChatMessage], 
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto"
    ) -> Any:
        """Génère une réponse intelligente avec support des outils."""
        
        system_prompt = {
            "role": "system",
            "content": self.system_prompt
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
                    "description": "Récupère l'état global des stocks et les risques. Permet de filtrer par catégorie ou statut.",
                    "parameters": {
                        "type": "object", 
                        "properties": {
                            "category": {"type": "string", "description": "Filtrer par catégorie (ex: 'Vêtements')"},
                            "status": {"type": "string", "enum": ["IN_STOCK", "OUT_OF_STOCK", "AT_RISK"], "description": "Filtrer par statut de stock"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_alerts",
                    "description": "Récupère les alertes de prévision et de rupture.",
                    "parameters": {
                        "type": "object", 
                        "properties": {
                            "severity": {"type": "string", "enum": ["HIGH", "MEDIUM", "LOW"], "description": "Filtrer par sévérité"}
                        }
                    }
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
                return [
                    {
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in message.tool_calls
                ]
            
            return message.content
        except Exception as e:
            logger.error(f"[OpenAIProvider] Generation Error: {e}")
            if "insufficient_quota" in str(e):
                return "Désolé, quota OpenAI dépassé. Veuillez vérifier votre abonnement."
            return f"Désolé, erreur technique : {str(e)}"

    async def stream_response(self, messages: List[ChatMessage], tools=None) -> Any:
        """Stream réel avec OpenAI"""
        openai_messages = [{"role": "system", "content": self.system_prompt}]
        for msg in messages:
            openai_messages.append({"role": msg.role.value, "content": msg.content})

        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                stream=True,
                temperature=0.7
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"[OpenAIProvider] Stream Error: {e}")
            if "insufficient_quota" in str(e):
                yield "Désolé, mais mon quota d'utilisation OpenAI a été dépassé. Veuillez vérifier votre abonnement ou passer à un autre fournisseur (Claude)."
            else:
                yield f"Désolé, une erreur est survenue lors de la génération de la réponse : {str(e)}"

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
