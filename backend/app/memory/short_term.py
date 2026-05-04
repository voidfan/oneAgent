"""Short-term memory - conversation context within a session."""
from collections import OrderedDict
from typing import Optional

from app.llm.base import LLMMessage


class ShortTermMemory:
    """Manages short-term conversation context with token-aware windowing."""

    def __init__(self, max_messages: int = 100, max_tokens: int = 32000):
        self.max_messages = max_messages
        self.max_tokens = max_tokens
        self._messages: list[LLMMessage] = []
        self._total_tokens: int = 0

    def add_message(self, message: LLMMessage, token_count: int = 0) -> None:
        """Add a message to short-term memory."""
        self._messages.append(message)
        self._total_tokens += token_count

        # Trim if exceeding limits (keep system messages)
        while (
            len(self._messages) > self.max_messages
            or self._total_tokens > self.max_tokens
        ):
            if len(self._messages) <= 1:
                break
            # Find first non-system message to remove
            for i, msg in enumerate(self._messages):
                if msg.role != "system":
                    self._messages.pop(i)
                    break
            else:
                break

    def get_messages(self) -> list[LLMMessage]:
        """Get all messages in short-term memory."""
        return list(self._messages)

    def get_recent(self, n: int = 10) -> list[LLMMessage]:
        """Get the most recent n messages."""
        return self._messages[-n:]

    def get_system_messages(self) -> list[LLMMessage]:
        """Get all system messages."""
        return [m for m in self._messages if m.role == "system"]

    def clear(self) -> None:
        """Clear all messages."""
        self._messages.clear()
        self._total_tokens = 0

    def summarize_context(self) -> str:
        """Create a summary of the conversation context."""
        parts = []
        for msg in self._messages[-20:]:  # Last 20 messages
            role = msg.role.upper()
            content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
            parts.append(f"[{role}]: {content}")
        return "\n".join(parts)

    @property
    def message_count(self) -> int:
        return len(self._messages)

    @property
    def total_tokens(self) -> int:
        return self._total_tokens
