from modules.chat.application.use_cases import ProcessUserMessageUseCase
from modules.chat.infrastructure.openai_adapter import OpenAIProvider
from modules.chat.infrastructure.anthropic_adapter import AnthropicProvider
from modules.chat.infrastructure.michi_api_adapter import MichiApiAdapter
from modules.chat.infrastructure.sql_repository import SQLAlchemyChatRepository
from modules.chat.infrastructure.adapters import MockLLMProvider, MockMichiApiAdapter
from core.config.settings import settings
from sqlalchemy.ext.asyncio import AsyncSession

class AssistantContainer:
    """Conteneur de dépendances pour l'Assistant (Pattern DI)"""
    def __init__(self):
        # Choix des adaptateurs selon l'environnement et priorité
        if settings.ANTHROPIC_API_KEY:
            self.llm_provider = AnthropicProvider()
        elif settings.OPENAI_API_KEY:
            self.llm_provider = OpenAIProvider()
        else:
            self.llm_provider = MockLLMProvider()



        # Michi API adapter
        self.michi_api = MichiApiAdapter()

    def get_process_message_use_case(self, db: AsyncSession) -> ProcessUserMessageUseCase:
        # On instancie le repo avec la session DB fournie par le context GraphQL
        repository = SQLAlchemyChatRepository(db)
        
        return ProcessUserMessageUseCase(
            llm_provider=self.llm_provider,
            michi_api=self.michi_api,
            repository=repository
        )

    def get_chat_repository(self, db: AsyncSession) -> SQLAlchemyChatRepository:
        return SQLAlchemyChatRepository(db)

# Instance globale pour le serveur
container = AssistantContainer()
