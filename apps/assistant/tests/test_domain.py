import pytest
from datetime import datetime
from src.modules.chat.domain.entities import ChatSession, ChatMessage, MessageRole

def test_chat_session_initialization():
    session = ChatSession(session_id="123", user_id="u1", org_id="o1")
    assert session.session_id == "123"
    assert len(session.messages) == 0

def test_add_message_to_session():
    session = ChatSession(session_id="123", user_id="u1", org_id="o1")
    session.add_message(MessageRole.USER, "Hello")
    
    assert len(session.messages) == 1
    assert session.messages[0].content == "Hello"
    assert session.messages[0].role == MessageRole.USER
    assert isinstance(session.messages[0].timestamp, datetime)

def test_chat_message_immutability():
    msg = ChatMessage(role=MessageRole.ASSISTANT, content="Hi")
    with pytest.raises(AttributeError):
        msg.content = "New" # Frozen dataclass
