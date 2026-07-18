from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Message:
    role: str
    content: str


@dataclass
class ConversationContext:
    messages: list[Message] = field(default_factory=list)
    total_tokens: int = 0


class ConversationMemory(ABC):

    @abstractmethod
    def add_message(self, role: str, content: str) -> None:
        ...

    @abstractmethod
    def get_history(self) -> list[Message]:
        ...

    @abstractmethod
    def clear(self) -> None:
        ...

    @property
    @abstractmethod
    def context_window(self) -> int:
        ...

    @context_window.setter
    @abstractmethod
    def context_window(self, size: int) -> None:
        ...


class InMemoryConversation(ConversationMemory):

    def __init__(self, context_window: int = 4096) -> None:
        self._messages: list[Message] = []
        self._context_window = context_window

    def add_message(self, role: str, content: str) -> None:
        self._messages.append(Message(role=role, content=content))
        self._trim()

    def get_history(self) -> list[Message]:
        return list(self._messages)

    def clear(self) -> None:
        self._messages.clear()

    @property
    def context_window(self) -> int:
        return self._context_window

    @context_window.setter
    def context_window(self, size: int) -> None:
        self._context_window = size

    def _trim(self) -> None:
        rough_token_count = sum(len(m.content.split()) for m in self._messages)
        while rough_token_count > self._context_window and self._messages:
            self._messages.pop(0)
            rough_token_count = sum(len(m.content.split()) for m in self._messages)


class SessionMemory(ABC):

    @abstractmethod
    def create_session(self, session_id: str) -> ConversationMemory:
        ...

    @abstractmethod
    def get_session(self, session_id: str) -> Optional[ConversationMemory]:
        ...

    @abstractmethod
    def delete_session(self, session_id: str) -> None:
        ...


class InMemorySessionMemory(SessionMemory):

    def __init__(self) -> None:
        self._sessions: dict[str, InMemoryConversation] = {}

    def create_session(self, session_id: str) -> ConversationMemory:
        mem = InMemoryConversation()
        self._sessions[session_id] = mem
        return mem

    def get_session(self, session_id: str) -> Optional[ConversationMemory]:
        return self._sessions.get(session_id)

    def delete_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
