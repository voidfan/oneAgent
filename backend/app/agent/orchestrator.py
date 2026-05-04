"""Multi-Agent Orchestrator - coordinates multiple agents for complex tasks."""
import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Optional

import structlog

from app.agent.engine import AgentEngine
from app.config import settings

logger = structlog.get_logger(__name__)


@dataclass
class AgentTask:
    """A task assigned to an agent."""
    id: str
    agent_id: str
    description: str
    depends_on: list[str] = field(default_factory=list)
    status: str = "pending"  # pending | running | completed | failed
    result: Optional[str] = None
    error: Optional[str] = None


class MultiAgentOrchestrator:
    """Orchestrates multiple agents working together on complex tasks.

    Supports:
    - Task distribution across agents
    - Dependency-aware execution
    - Parallel execution of independent tasks
    - Result aggregation
    - Inter-agent communication via shared memory
    """

    def __init__(self):
        self._agents: dict[str, AgentEngine] = {}
        self._tasks: dict[str, AgentTask] = {}
        self._results: dict[str, str] = {}
        self._semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_AGENTS)

    def register_agent(self, agent_id: str, engine: AgentEngine) -> None:
        """Register an agent with the orchestrator."""
        self._agents[agent_id] = engine
        logger.info("agent_registered", agent_id=agent_id)

    def create_agent(
        self,
        name: str,
        system_prompt: str,
        llm_provider: Optional[str] = None,
        llm_model: Optional[str] = None,
        tool_names: Optional[list[str]] = None,
    ) -> AgentEngine:
        """Create and register a new agent."""
        agent_id = f"agent_{name}_{uuid.uuid4().hex[:8]}"
        engine = AgentEngine(
            agent_id=agent_id,
            system_prompt=system_prompt,
            llm_provider=llm_provider,
            llm_model=llm_model,
            tool_names=tool_names,
        )
        self.register_agent(agent_id, engine)
        return engine

    def add_task(
        self,
        agent_id: str,
        description: str,
        depends_on: Optional[list[str]] = None,
    ) -> str:
        """Add a task for an agent."""
        task_id = str(uuid.uuid4())
        task = AgentTask(
            id=task_id,
            agent_id=agent_id,
            description=description,
            depends_on=depends_on or [],
        )
        self._tasks[task_id] = task
        return task_id

    async def execute_all(self) -> dict[str, str]:
        """Execute all tasks respecting dependencies.

        Returns:
            Dictionary mapping task_id to result.
        """
        completed = set()
        failed = set()

        while True:
            # Find tasks ready to execute
            ready_tasks = [
                task for task in self._tasks.values()
                if task.status == "pending"
                and all(dep in completed for dep in task.depends_on)
                and not any(dep in failed for dep in task.depends_on)
            ]

            # Mark tasks with failed dependencies
            for task in self._tasks.values():
                if task.status == "pending" and any(dep in failed for dep in task.depends_on):
                    task.status = "failed"
                    task.error = "Dependency failed"
                    failed.add(task.id)

            if not ready_tasks:
                # Check if all tasks are done
                pending = [t for t in self._tasks.values() if t.status == "pending"]
                if not pending:
                    break
                # Deadlock detection
                logger.error("orchestrator_deadlock", pending_tasks=len(pending))
                break

            # Execute ready tasks in parallel
            tasks_coros = [
                self._execute_task(task) for task in ready_tasks
            ]
            results = await asyncio.gather(*tasks_coros, return_exceptions=True)

            for task, result in zip(ready_tasks, results):
                if isinstance(result, Exception):
                    task.status = "failed"
                    task.error = str(result)
                    failed.add(task.id)
                    logger.error("task_failed", task_id=task.id, error=str(result))
                else:
                    task.status = "completed"
                    task.result = result
                    completed.add(task.id)
                    self._results[task.id] = result
                    logger.info("task_completed", task_id=task.id)

        return self._results

    async def _execute_task(self, task: AgentTask) -> str:
        """Execute a single task with concurrency control."""
        async with self._semaphore:
            agent = self._agents.get(task.agent_id)
            if not agent:
                raise ValueError(f"Agent '{task.agent_id}' not found")

            task.status = "running"
            logger.info("task_started", task_id=task.id, agent_id=task.agent_id)

            # Build context from dependency results
            context_parts = []
            for dep_id in task.depends_on:
                dep_result = self._results.get(dep_id)
                if dep_result:
                    context_parts.append(f"[Result from previous task]: {dep_result}")

            message = task.description
            if context_parts:
                message += "\n\nContext from previous tasks:\n" + "\n".join(context_parts)

            return await agent.run(message, task_id=task.id)

    async def run_pipeline(self, tasks: list[dict]) -> dict[str, str]:
        """Run a pipeline of tasks with automatic agent assignment.

        Args:
            tasks: List of task dicts with 'description', 'agent_config', 'depends_on'.

        Returns:
            Results dictionary.
        """
        task_ids = []
        for task_def in tasks:
            agent_config = task_def.get("agent_config", {})
            agent = self.create_agent(
                name=agent_config.get("name", "worker"),
                system_prompt=agent_config.get("system_prompt", ""),
                llm_provider=agent_config.get("llm_provider"),
                llm_model=agent_config.get("llm_model"),
                tool_names=agent_config.get("tool_names"),
            )

            # Map dependency indices to task IDs
            depends_on = []
            for dep_idx in task_def.get("depends_on", []):
                if dep_idx < len(task_ids):
                    depends_on.append(task_ids[dep_idx])

            task_id = self.add_task(
                agent_id=agent.agent_id,
                description=task_def["description"],
                depends_on=depends_on,
            )
            task_ids.append(task_id)

        return await self.execute_all()

    def get_status(self) -> dict:
        """Get current orchestration status."""
        return {
            "agents": len(self._agents),
            "tasks": {
                "total": len(self._tasks),
                "pending": sum(1 for t in self._tasks.values() if t.status == "pending"),
                "running": sum(1 for t in self._tasks.values() if t.status == "running"),
                "completed": sum(1 for t in self._tasks.values() if t.status == "completed"),
                "failed": sum(1 for t in self._tasks.values() if t.status == "failed"),
            },
        }
