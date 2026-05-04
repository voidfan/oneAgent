"""Anthropic (Claude) LLM provider."""
import json
from typing import AsyncIterator, Optional

from anthropic import AsyncAnthropic

from app.llm.base import BaseLLMProvider, LLMMessage, LLMResponse


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude API provider."""

    def __init__(
        self,
        model: str = "claude-3-sonnet-20240229",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs
    ):
        super().__init__(model=model, **kwargs)
        client_kwargs = {}
        if api_key:
            client_kwargs["api_key"] = api_key
        if base_url:
            client_kwargs["base_url"] = base_url
        self.client = AsyncAnthropic(**client_kwargs)

    def _convert_messages_anthropic(self, messages: list[LLMMessage]) -> tuple[str, list[dict]]:
        """Convert to Anthropic format: separate system prompt from messages."""
        system_prompt = ""
        converted = []
        for msg in messages:
            if msg.role == "system":
                system_prompt += msg.content + "\n"
            elif msg.role == "tool":
                converted.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": msg.tool_call_id,
                            "content": msg.content,
                        }
                    ],
                })
            else:
                converted.append({"role": msg.role, "content": msg.content})
        return system_prompt.strip(), converted

    def _convert_tools_anthropic(self, tools: Optional[list[dict]]) -> Optional[list[dict]]:
        """Convert OpenAI-style tools to Anthropic format."""
        if not tools:
            return None
        anthropic_tools = []
        for tool in tools:
            if tool.get("type") == "function":
                func = tool["function"]
                anthropic_tools.append({
                    "name": func["name"],
                    "description": func.get("description", ""),
                    "input_schema": func.get("parameters", {"type": "object", "properties": {}}),
                })
        return anthropic_tools

    async def chat(
        self,
        messages: list[LLMMessage],
        tools: Optional[list[dict]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        system_prompt, converted_messages = self._convert_messages_anthropic(messages)

        request_kwargs = {
            "model": self.model,
            "messages": converted_messages,
            "max_tokens": max_tokens or 4096,
            "temperature": temperature,
        }
        if system_prompt:
            request_kwargs["system"] = system_prompt

        anthropic_tools = self._convert_tools_anthropic(tools)
        if anthropic_tools:
            request_kwargs["tools"] = anthropic_tools

        response = await self.client.messages.create(**request_kwargs)

        content = ""
        tool_calls = []
        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "type": "function",
                    "function": {
                        "name": block.name,
                        "arguments": json.dumps(block.input),
                    },
                })

        return LLMResponse(
            content=content,
            role="assistant",
            tool_calls=tool_calls,
            finish_reason=response.stop_reason,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
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
        system_prompt, converted_messages = self._convert_messages_anthropic(messages)

        request_kwargs = {
            "model": self.model,
            "messages": converted_messages,
            "max_tokens": max_tokens or 4096,
            "temperature": temperature,
        }
        if system_prompt:
            request_kwargs["system"] = system_prompt

        async with self.client.messages.stream(**request_kwargs) as stream:
            async for text in stream.text_stream:
                yield text

    async def count_tokens(self, text: str) -> int:
        # Anthropic doesn't provide a public tokenizer; rough estimate
        return len(text) // 4
