"""Local LLM provider (compatible with OpenAI API format, e.g., Ollama, vLLM, LM Studio)."""
from typing import AsyncIterator, Optional

import httpx

from app.config import settings
from app.llm.base import BaseLLMProvider, LLMMessage, LLMResponse


class LocalLLMProvider(BaseLLMProvider):
    """Local LLM provider using OpenAI-compatible API."""

    def __init__(self, model: Optional[str] = None, **kwargs):
        super().__init__(model=model or settings.LOCAL_LLM_MODEL or "local-model", **kwargs)
        self.base_url = settings.LOCAL_LLM_URL or "http://localhost:11434/v1"

    async def chat(
        self,
        messages: list[LLMMessage],
        tools: Optional[list[dict]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        payload = {
            "model": self.model,
            "messages": self._convert_messages(messages),
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        choice = data["choices"][0]
        message = choice["message"]

        tool_calls = []
        if message.get("tool_calls"):
            for tc in message["tool_calls"]:
                tool_calls.append({
                    "id": tc.get("id", ""),
                    "type": "function",
                    "function": {
                        "name": tc["function"]["name"],
                        "arguments": tc["function"]["arguments"],
                    },
                })

        usage = data.get("usage", {})
        return LLMResponse(
            content=message.get("content", "") or "",
            role="assistant",
            tool_calls=tool_calls,
            finish_reason=choice.get("finish_reason"),
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
            model=data.get("model", self.model),
            raw_response=data,
        )

    async def chat_stream(
        self,
        messages: list[LLMMessage],
        tools: Optional[list[dict]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        payload = {
            "model": self.model,
            "messages": self._convert_messages(messages),
            "temperature": temperature,
            "stream": True,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=payload,
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        import json
                        data = json.loads(data_str)
                        delta = data["choices"][0].get("delta", {})
                        if delta.get("content"):
                            yield delta["content"]

    async def count_tokens(self, text: str) -> int:
        # Rough estimate for local models
        return len(text) // 4
