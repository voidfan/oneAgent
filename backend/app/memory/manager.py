"""Memory manager - unified interface for all memory types."""
from typing import Any, Optional

import structlog

from app.memory.short_term import ShortTermMemory
from app.memory.long_term import LongTermMemory
from app.memory.working import WorkingMemory
from app.llm.base import LLMMessage

logger = structlog.get_logger(__name__)


class MemoryManager:
    """Unified memory manager combining short-term, long-term, and working memory."""

    def __init__(self, agent_id: Optional[str] = None):
        self.agent_id = agent_id
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory(
            collection_name=f"agent_{agent_id}" if agent_id else "default"
        )
        self.working = WorkingMemory()

    def add_message(self, message: LLMMessage, token_count: int = 0) -> None:
        """Add a message to short-term memory."""
        self.short_term.add_message(message, token_count)

    def get_messages(self) -> list[LLMMessage]:
        """Get conversation messages from short-term memory."""
        return self.short_term.get_messages()

    async def store_knowledge(self, key: str, content: str, metadata: Optional[dict] = None) -> str:
        """Store knowledge in long-term memory."""
        return await self.long_term.store(key, content, metadata)

    async def recall(self, query: str, n_results: int = 5) -> list[dict]:
        """Recall relevant knowledge from long-term memory."""
        return await self.long_term.retrieve(query, n_results)

    def create_task(self, task_id: str, goal: str):
        """Create a task in working memory."""
        return self.working.create_task(task_id, goal)

    def get_working_context(self, task_id: str) -> str:
        """Get working memory context for a task."""
        return self.working.get_context_summary(task_id)

    async def build_context(self, task_id: Optional[str] = None, query: Optional[str] = None) -> str:
        """Build a comprehensive context string from all memory types."""
        parts = []

        # Working memory context
        if task_id:
            working_ctx = self.working.get_context_summary(task_id)
            if working_ctx:
                parts.append(f"[Working Memory]\n{working_ctx}")

        # Long-term memory recall
        if query:
            try:
                memories = await self.long_term.retrieve(query, n_results=3)
                if memories:
                    mem_str = "\n".join(
                        f"- {m['content'][:200]}" for m in memories
                    )
                    parts.append(f"[Relevant Knowledge]\n{mem_str}")
            except Exception as e:
                logger.warning("long_term_recall_failed", error=str(e))

        return "\n\n".join(parts)

    def clear_session(self) -> None:
        """Clear short-term and working memory (keep long-term)."""
        self.short_term.clear()
        self.working.clear_all()

    def clear_all(self) -> None:
        """Clear all memory types."""
        self.short_term.clear()
        self.working.clear_all()
