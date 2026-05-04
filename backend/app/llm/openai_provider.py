"""OpenAI LLM provider - also compatible with OpenAI-compatible APIs."""
import json
from typing import AsyncIterator, Optional

from openai import AsyncOpenAI

from app.llm.base import BaseLLMProvider, LLMMessage, LLMResponse


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider (also compatible with OpenAI-compatible APIs like DeepSeek, Moonshot, etc.)."""

    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs
    ):
        super().__init__(model=model, **kwargs)
        self.client = AsyncOpenAI(
            api_key=api_key or "sk-placeholder",
            base_url=base_url if base_url else None,
        )

    async def chat(
        self,
        messages: list[LLMMessage],
        tools: Optional[list[dict]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        request_kwargs = {
            "model": self.model,
            "messages": self._convert_messages(messages),
            "temperature": temperature,
        }
        if max_tokens:
            request_kwargs["max_tokens"] = max_tokens
        if tools:
            request_kwargs["tools"] = tools
            request_kwargs["tool_choice"] = kwargs.get("tool_choice", "auto")

        response = await self.client.chat.completions.create(**request_kwargs)
        choice = response.choices[0]

        tool_calls = []
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                tool_calls.append({
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                })

        return LLMResponse(
            content=choice.message.content or "",
            role="assistant",
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            },
            model=response.model,
            raw_response=response,
        )

    async def chat_stream(
        self,
        messages: list[LLMMessage],
        tools: Optional[list[dict]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        request_kwargs = {
            "model": self.model,
            "messages": self._convert_messages(messages),
            "temperature": temperature,
            "stream": True,
        }
        if max_tokens:
            request_kwargs["max_tokens"] = max_tokens
        if tools:
            request_kwargs["tools"] = tools

        stream = await self.client.chat.completions.create(**request_kwargs)
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def count_tokens(self, text: str) -> int:
        try:
            import tiktoken
            encoding = tiktoken.encoding_for_model(self.model)
            return len(encoding.encode(text))
        except Exception:
            # Rough estimate: ~4 chars per token
            return len(text) // 4
