"""Base LLM provider interface."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Optional


@dataclass
class LLMMessage:
    """Unified message format for LLM communication."""
    role: str  # system | user | assistant | tool
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_calls: Optional[list[dict]] = None


@dataclass
class LLMResponse:
    """Unified response from LLM providers."""
    content: str
    role: str = "assistant"
    tool_calls: list[dict] = field(default_factory=list)
    finish_reason: Optional[str] = None
    usage: dict = field(default_factory=dict)  # {prompt_tokens, completion_tokens, total_tokens}
    model: Optional[str] = None
    raw_response: Optional[Any] = None

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0

    @property
    def total_tokens(self) -> int:
        return self.usage.get("total_tokens", 0)


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, model: Optional[str] = None, **kwargs):
        self.model = model
        self.kwargs = kwargs

    @abstractmethod
    async def chat(
        self,
        messages: list[LLMMessage],
        tools: Optional[list[dict]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        """Send a chat completion request."""
        ...

    @abstractmethod
    async def chat_stream(
        self,
        messages: list[LLMMessage],
        tools: Optional[list[dict]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Send a streaming chat completion request."""
        ...

    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        ...

    def _convert_messages(self, messages: list[LLMMessage]) -> list[dict]:
        """Convert LLMMessage list to provider-specific format. Override in subclass."""
        result = []
        for msg in messages:
            d = {"role": msg.role, "content": msg.content}
            if msg.name:
                d["name"] = msg.name
            if msg.tool_call_id:
                d["tool_call_id"] = msg.tool_call_id
            if msg.tool_calls:
                d["tool_calls"] = msg.tool_calls
            result.append(d)
        return result
