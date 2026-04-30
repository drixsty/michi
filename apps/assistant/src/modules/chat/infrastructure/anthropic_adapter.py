import anthropic
from typing import List, Dict, Any, Optional
from loguru import logger
from modules.chat.domain.entities import ChatMessage, MessageRole
from modules.chat.domain.ports import ILLMProvider
from core.config.settings import settings

class AnthropicProvider(ILLMProvider):
    def __init__(self):
        logger.info("[AnthropicProvider] Initializing Claude 3.5 Sonnet")
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-3-5-sonnet-20240620"
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
        """Génère une réponse avec Claude 3.5 Sonnet."""
        
        system_prompt = self.system_prompt

        anthropic_messages = []
        for msg in messages:
            anthropic_messages.append({"role": "user" if msg.role == MessageRole.USER else "assistant", "content": msg.content})

        # Conversion des outils au format Anthropic si nécessaire
        # Pour l'instant on simplifie l'appel outils comme OpenAI
        # Note: Anthropic a une syntaxe légèrement différente pour les outils
        
        claude_tools = [
            {
                "name": "get_inventory",
                "description": "Récupère l'état global des stocks et les risques. Permet de filtrer par catégorie ou statut.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "category": {"type": "string", "description": "Filtrer par catégorie (ex: 'Vêtements')"},
                        "status": {"type": "string", "enum": ["IN_STOCK", "OUT_OF_STOCK", "AT_RISK"], "description": "Filtrer par statut de stock"}
                    }
                }
            },
            {
                "name": "get_alerts",
                "description": "Récupère les alertes de prévision et de rupture.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "severity": {"type": "string", "enum": ["HIGH", "MEDIUM", "LOW"], "description": "Filtrer par sévérité"}
                    }
                }
            }
        ]

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=anthropic_messages,
                tools=claude_tools
            )
            
            # Gestion des Tool Calls chez Anthropic
            tool_calls = [content for content in response.content if content.type == "tool_use"]
            if tool_calls:
                import json
                # On adapte au format attendu par l'orchestrateur
                return [{"function": {"name": tc.name, "arguments": json.dumps(tc.input)}} for tc in tool_calls]
            
            # Texte normal
            text_contents = [content.text for content in response.content if content.type == "text"]
            return " ".join(text_contents) if text_contents else "Désolé, je ne peux pas répondre."

        except Exception as e:
            logger.error(f"[AnthropicProvider] Error: {str(e)}")
            return "Désolé, je rencontre une erreur technique avec Claude."

    async def stream_response(
        self, 
        messages: List[ChatMessage], 
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto"
    ) -> Any:
        """Stream les réponses de Claude."""
        system_prompt = self.system_prompt
        anthropic_messages = []
        for msg in messages:
            anthropic_messages.append({"role": "user" if msg.role == MessageRole.USER else "assistant", "content": msg.content})

        # Pour le streaming avec outils chez Anthropic, c'est plus complexe.
        # Pour cette phase on simplifie le streaming au texte uniquement.
        try:
            async with self.client.messages.stream(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=anthropic_messages,
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            logger.error(f"[AnthropicProvider] Stream Error: {str(e)}")
            yield "Erreur de streaming."

    async def classify_intent(self, user_input: str) -> str:
        """Classification rapide via Claude Haiku ou Sonnet."""
        prompt = f"Analyse l'intention de cette phrase : '{user_input}'. Répond uniquement par QUERY_INVENTORY, QUERY_ALERTS ou GENERAL_CHAT."
        
        try:
            response = await self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text.strip()
        except Exception:
            return "GENERAL_CHAT"
