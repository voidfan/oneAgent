"""Working memory - intermediate state during task execution."""
from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime


@dataclass
class TaskState:
    """State of a task being executed."""
    goal: str
    plan: list[str] = field(default_factory=list)
    current_step: int = 0
    observations: list[str] = field(default_factory=list)
    reflections: list[str] = field(default_factory=list)
    variables: dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending | running | completed | failed


class WorkingMemory:
    """Manages intermediate state during agent task execution."""

    def __init__(self):
        self._tasks: dict[str, TaskState] = {}
        self._scratchpad: dict[str, Any] = {}

    def create_task(self, task_id: str, goal: str) -> TaskState:
        """Create a new task in working memory."""
        task = TaskState(goal=goal, status="running")
        self._tasks[task_id] = task
        return task

    def get_task(self, task_id: str) -> Optional[TaskState]:
        """Get task state."""
        return self._tasks.get(task_id)

    def update_plan(self, task_id: str, plan: list[str]) -> None:
        """Update the plan for a task."""
        task = self._tasks.get(task_id)
        if task:
            task.plan = plan

    def advance_step(self, task_id: str) -> None:
        """Move to the next step in the plan."""
        task = self._tasks.get(task_id)
        if task:
            task.current_step += 1

    def add_observation(self, task_id: str, observation: str) -> None:
        """Add an observation from tool execution or reasoning."""
        task = self._tasks.get(task_id)
        if task:
            task.observations.append(observation)

    def add_reflection(self, task_id: str, reflection: str) -> None:
        """Add a reflection/self-evaluation."""
        task = self._tasks.get(task_id)
        if task:
            task.reflections.append(reflection)

    def set_variable(self, task_id: str, key: str, value: Any) -> None:
        """Store a variable in working memory."""
        task = self._tasks.get(task_id)
        if task:
            task.variables[key] = value

    def get_variable(self, task_id: str, key: str) -> Optional[Any]:
        """Retrieve a variable from working memory."""
        task = self._tasks.get(task_id)
        if task:
            return task.variables.get(key)
        return None

    def complete_task(self, task_id: str) -> None:
        """Mark a task as completed."""
        task = self._tasks.get(task_id)
        if task:
            task.status = "completed"

    def fail_task(self, task_id: str) -> None:
        """Mark a task as failed."""
        task = self._tasks.get(task_id)
        if task:
            task.status = "failed"

    def get_context_summary(self, task_id: str) -> str:
        """Get a summary of the current working memory for context injection."""
        task = self._tasks.get(task_id)
        if not task:
            return ""

        parts = [f"Goal: {task.goal}"]

        if task.plan:
            plan_str = "\n".join(
                f"  {'✓' if i < task.current_step else '→' if i == task.current_step else '○'} {step}"
                for i, step in enumerate(task.plan)
            )
            parts.append(f"Plan:\n{plan_str}")

        if task.observations:
            recent = task.observations[-5:]
            parts.append(f"Recent observations:\n" + "\n".join(f"  - {o}" for o in recent))

        if task.reflections:
            parts.append(f"Latest reflection: {task.reflections[-1]}")

        if task.variables:
            var_str = ", ".join(f"{k}={v}" for k, v in list(task.variables.items())[:10])
            parts.append(f"Variables: {var_str}")

        return "\n\n".join(parts)

    # Scratchpad for temporary data
    def scratch_set(self, key: str, value: Any) -> None:
        self._scratchpad[key] = value

    def scratch_get(self, key: str) -> Optional[Any]:
        return self._scratchpad.get(key)

    def scratch_clear(self) -> None:
        self._scratchpad.clear()

    def clear_task(self, task_id: str) -> None:
        """Remove a task from working memory."""
        self._tasks.pop(task_id, None)

    def clear_all(self) -> None:
        """Clear all working memory."""
        self._tasks.clear()
        self._scratchpad.clear()
