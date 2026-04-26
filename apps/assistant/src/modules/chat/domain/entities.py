from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

class MessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

@dataclass(frozen=True)
class ChatMessage:
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class ChatSession:
    session_id: str
    user_id: str
    org_id: str
    messages: List[ChatMessage] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_message(self, role: MessageRole, content: str):
        self.messages.append(ChatMessage(role=role, content=content))

@dataclass(frozen=True)
class AssistantAction:
    """Représente une action que l'assistant décide de prendre (Tool Call)"""
    tool_name: str
    arguments: Dict[str, Any]
