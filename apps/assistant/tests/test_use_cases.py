import pytest
from unittest.mock import AsyncMock, MagicMock
from src.modules.chat.application.use_cases import ProcessUserMessageUseCase
from src.modules.chat.domain.entities import ChatSession, MessageRole

@pytest.mark.asyncio
async def test_process_user_message_flow():
    # Setup Mocks
    llm_provider = AsyncMock()
    llm_provider.classify_intent.return_value = "GENERAL_CHAT"
    llm_provider.generate_response.return_value = "Réponse IA"
    
    michi_api = AsyncMock()
    
    repository = AsyncMock()
    repository.get_session.return_value = None # Nouvelle session
    
    use_case = ProcessUserMessageUseCase(llm_provider, michi_api, repository)
    
    # Execute
    response = await use_case.execute(
        session_id="s1", 
        user_id="u1", 
        org_id="o1", 
        content="Hello",
        jwt="token"
    )
    
    # Assertions
    assert response == "Réponse IA"
    repository.save_session.assert_called_once()
    llm_provider.generate_response.assert_called_once()
    
    # Vérifier que le message a été ajouté à la session sauvegardée
    saved_session = repository.save_session.call_args[0][0]
    assert len(saved_session.messages) == 2
    assert saved_session.messages[0].content == "Hello"
    assert saved_session.messages[1].content == "Réponse IA"

@pytest.mark.asyncio
async def test_inventory_intent_calls_michi_api():
    llm_provider = AsyncMock()
    llm_provider.classify_intent.return_value = "QUERY_INVENTORY"
    llm_provider.generate_response.return_value = "Voici votre stock"
    
    michi_api = AsyncMock()
    michi_api.get_inventory_status.return_value = {"stock": 10}
    
    repository = AsyncMock()
    repository.get_session.return_value = ChatSession("s1", "u1", "o1")
    
    use_case = ProcessUserMessageUseCase(llm_provider, michi_api, repository)
    
    await use_case.execute("s1", "u1", "o1", "Mon stock ?", "token")
    
    # Michi API doit avoir été appelée
    michi_api.get_inventory_status.assert_called_once_with("o1", "token")
