"""Core Agent Engine - the main reasoning and execution loop."""
import json
import time
import uuid
from typing import AsyncIterator, Optional, Callable

import structlog

from app.config import settings
from app.llm.base import BaseLLMProvider, LLMMessage, LLMResponse
from app.llm.factory import get_llm_provider
from app.memory.manager import MemoryManager
from app.tools.manager import ToolManager
from app.agent.planner import Planner

logger = structlog.get_logger(__name__)


class AgentEngine:
    """Core agent engine implementing the Think-Plan-Act-Observe loop.

    The agent follows a ReAct-style loop:
    1. Think: Analyze the current situation
    2. Plan: Decompose the task if needed
    3. Act: Execute a tool or generate a response
    4. Observe: Process the result and decide next step
    5. Reflect: Periodically evaluate progress
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        llm_provider: Optional[str] = None,
        llm_model: Optional[str] = None,
        max_steps: int = 50,
        temperature: float = 0.7,
        tool_names: Optional[list[str]] = None,
        on_step: Optional[Callable] = None,
    ):
        self.agent_id = agent_id or str(uuid.uuid4())
        self.system_prompt = system_prompt or self._default_system_prompt()
        self.max_steps = min(max_steps, settings.MAX_AGENT_STEPS)
        self.temperature = temperature
        self.tool_names = tool_names

        # Components
        self.llm: BaseLLMProvider = get_llm_provider(llm_provider, llm_model)
        self.memory = MemoryManager(agent_id=self.agent_id)
        self.tool_manager = ToolManager()
        self.planner = Planner(self.llm)

        # Callbacks
        self.on_step = on_step

        # State
        self._step_count = 0
        self._total_tokens = 0
        self._is_running = False

    def _default_system_prompt(self) -> str:
        return """You are an intelligent AI agent capable of solving complex tasks step by step.

You have access to tools that you can use to gather information and take actions.
When given a task:
1. Think about what needs to be done
2. Break it down into steps if complex
3. Use available tools when needed
4. Observe the results and adjust your approach
5. Provide a clear, comprehensive response

Always explain your reasoning. If you're unsure, say so.
When using tools, provide the exact parameters needed.
After completing the task, summarize what you did and the results."""

    async def run(self, user_message: str, task_id: Optional[str] = None) -> str:
        """Run the agent with a user message and return the final response.

        Args:
            user_message: The user's input message.
            task_id: Optional task ID for tracking.

        Returns:
            The agent's final response string.
        """
        task_id = task_id or str(uuid.uuid4())
        self._is_running = True
        self._step_count = 0

        # Initialize memory
        self.memory.add_message(LLMMessage(role="system", content=self.system_prompt))
        self.memory.add_message(LLMMessage(role="user", content=user_message))
        self.memory.create_task(task_id, goal=user_message)

        # Get tool schemas
        tool_schemas = self.tool_manager.get_tool_schemas(self.tool_names)

        try:
            while self._step_count < self.max_steps and self._is_running:
                self._step_count += 1

                # Build context from memory
                context = await self.memory.build_context(task_id, user_message)
                messages = self.memory.get_messages()

                # Inject working memory context if available
                if context:
                    context_msg = LLMMessage(
                        role="system",
                        content=f"[Current Context]\n{context}",
                    )
                    messages = messages + [context_msg]

                # Call LLM
                start_time = time.monotonic()
                response = await self.llm.chat(
                    messages=messages,
                    tools=tool_schemas if tool_schemas else None,
                    temperature=self.temperature,
                )
                duration_ms = int((time.monotonic() - start_time) * 1000)
                self._total_tokens += response.total_tokens

                # Log step
                step_info = {
                    "step": self._step_count,
                    "has_tool_calls": response.has_tool_calls,
                    "tokens": response.total_tokens,
                    "duration_ms": duration_ms,
                }
                logger.info("agent_step", **step_info)

                if self.on_step:
                    await self._safe_callback(step_info)

                # If no tool calls, this is the final response
                if not response.has_tool_calls:
                    self.memory.add_message(
                        LLMMessage(role="assistant", content=response.content)
                    )
                    self.memory.working.complete_task(task_id)
                    self._is_running = False
                    return response.content

                # Process tool calls
                self.memory.add_message(
                    LLMMessage(
                        role="assistant",
                        content=response.content,
                        tool_calls=response.tool_calls,
                    )
                )

                for tool_call in response.tool_calls:
                    func = tool_call["function"]
                    tool_name = func["name"]
                    arguments = func["arguments"]

                    logger.info(
                        "tool_call",
                        tool=tool_name,
                        step=self._step_count,
                    )

                    # Execute tool
                    result = await self.tool_manager.execute_tool(
                        tool_name=tool_name,
                        arguments=arguments,
                        execution_id=task_id,
                    )

                    # Add observation to memory
                    observation = result.to_str()
                    self.memory.add_message(
                        LLMMessage(
                            role="tool",
                            content=observation,
                            tool_call_id=tool_call["id"],
                            name=tool_name,
                        )
                    )
                    self.memory.working.add_observation(
                        task_id, f"[{tool_name}]: {observation[:500]}"
                    )

                # Periodic reflection (every 5 steps)
                if self._step_count % 5 == 0:
                    await self._reflect(task_id)

            # Max steps reached
            self.memory.working.fail_task(task_id)
            return f"I've reached the maximum number of steps ({self.max_steps}). Here's what I've accomplished so far:\n\n{self.memory.working.get_context_summary(task_id)}"

        except Exception as e:
            logger.error("agent_error", error=str(e), step=self._step_count)
            self.memory.working.fail_task(task_id)
            raise
        finally:
            self._is_running = False

    async def run_stream(self, user_message: str, task_id: Optional[str] = None) -> AsyncIterator[str]:
        """Run the agent with streaming output."""
        task_id = task_id or str(uuid.uuid4())
        self._is_running = True
        self._step_count = 0

        self.memory.add_message(LLMMessage(role="system", content=self.system_prompt))
        self.memory.add_message(LLMMessage(role="user", content=user_message))
        self.memory.create_task(task_id, goal=user_message)

        tool_schemas = self.tool_manager.get_tool_schemas(self.tool_names)

        try:
            while self._step_count < self.max_steps and self._is_running:
                self._step_count += 1
                messages = self.memory.get_messages()

                # Try non-streaming first to handle tool calls
                response = await self.llm.chat(
                    messages=messages,
                    tools=tool_schemas if tool_schemas else None,
                    temperature=self.temperature,
                )
                self._total_tokens += response.total_tokens

                if not response.has_tool_calls:
                    # Stream the final response
                    async for chunk in self.llm.chat_stream(
                        messages=messages,
                        temperature=self.temperature,
                    ):
                        yield chunk
                    self.memory.working.complete_task(task_id)
                    self._is_running = False
                    return

                # Process tool calls (same as non-streaming)
                self.memory.add_message(
                    LLMMessage(
                        role="assistant",
                        content=response.content,
                        tool_calls=response.tool_calls,
                    )
                )

                for tool_call in response.tool_calls:
                    func = tool_call["function"]
                    tool_name = func["name"]
                    yield f"\n🔧 Using tool: {tool_name}...\n"

                    result = await self.tool_manager.execute_tool(
                        tool_name=tool_name,
                        arguments=func["arguments"],
                        execution_id=task_id,
                    )

                    self.memory.add_message(
                        LLMMessage(
                            role="tool",
                            content=result.to_str(),
                            tool_call_id=tool_call["id"],
                            name=tool_name,
                        )
                    )

        except Exception as e:
            yield f"\n❌ Error: {str(e)}"
            self.memory.working.fail_task(task_id)
        finally:
            self._is_running = False

    async def _reflect(self, task_id: str) -> None:
        """Periodic self-reflection to evaluate progress."""
        context = self.memory.working.get_context_summary(task_id)
        reflection_prompt = LLMMessage(
            role="system",
            content=f"""Briefly reflect on your progress so far:
{context}

Are you making good progress? Should you adjust your approach?
Respond in 1-2 sentences.""",
        )

        try:
            response = await self.llm.chat(
                messages=[reflection_prompt],
                temperature=0.3,
                max_tokens=200,
            )
            self.memory.working.add_reflection(task_id, response.content)
            logger.info("agent_reflection", step=self._step_count, reflection=response.content[:100])
        except Exception as e:
            logger.warning("reflection_failed", error=str(e))

    async def _safe_callback(self, data: dict) -> None:
        """Safely invoke callback."""
        try:
            if self.on_step:
                result = self.on_step(data)
                if hasattr(result, "__await__"):
                    await result
        except Exception as e:
            logger.warning("callback_error", error=str(e))

    def stop(self) -> None:
        """Stop the agent execution."""
        self._is_running = False

    @property
    def step_count(self) -> int:
        return self._step_count

    @property
    def total_tokens(self) -> int:
        return self._total_tokens
