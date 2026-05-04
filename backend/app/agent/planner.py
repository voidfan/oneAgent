"""Task planner - decomposes complex tasks into executable sub-tasks."""
import json
from typing import Optional

import structlog

from app.llm.base import BaseLLMProvider, LLMMessage

logger = structlog.get_logger(__name__)

PLANNING_PROMPT = """You are a task planning assistant. Given a complex goal, break it down into a clear, ordered list of sub-tasks.

Rules:
1. Each sub-task should be specific and actionable
2. Sub-tasks should be in logical execution order
3. Include dependencies between tasks if any
4. Keep the plan concise (max 10 steps)
5. Each step should be achievable with available tools

Respond in JSON format:
{
    "analysis": "Brief analysis of the goal",
    "plan": [
        {"step": 1, "task": "description", "depends_on": []},
        {"step": 2, "task": "description", "depends_on": [1]}
    ],
    "estimated_complexity": "low|medium|high"
}"""


class Planner:
    """Decomposes complex tasks into executable plans."""

    def __init__(self, llm: BaseLLMProvider):
        self.llm = llm

    async def create_plan(self, goal: str, context: Optional[str] = None) -> dict:
        """Create an execution plan for a given goal.

        Args:
            goal: The high-level goal to plan for.
            context: Optional additional context.

        Returns:
            Plan dictionary with analysis, steps, and complexity.
        """
        messages = [
            LLMMessage(role="system", content=PLANNING_PROMPT),
        ]

        user_content = f"Goal: {goal}"
        if context:
            user_content += f"\n\nAdditional context:\n{context}"

        messages.append(LLMMessage(role="user", content=user_content))

        try:
            response = await self.llm.chat(
                messages=messages,
                temperature=0.3,
                max_tokens=1000,
            )

            # Parse JSON response
            plan = json.loads(response.content)
            logger.info(
                "plan_created",
                goal=goal[:100],
                steps=len(plan.get("plan", [])),
                complexity=plan.get("estimated_complexity"),
            )
            return plan

        except json.JSONDecodeError:
            # If LLM doesn't return valid JSON, create a simple plan
            logger.warning("plan_parse_failed", goal=goal[:100])
            return {
                "analysis": "Could not create structured plan",
                "plan": [{"step": 1, "task": goal, "depends_on": []}],
                "estimated_complexity": "unknown",
            }
        except Exception as e:
            logger.error("planning_failed", error=str(e))
            raise

    async def replan(
        self,
        original_goal: str,
        completed_steps: list[str],
        current_state: str,
        error: Optional[str] = None,
    ) -> dict:
        """Dynamically adjust the plan based on execution results.

        Args:
            original_goal: The original goal.
            completed_steps: Steps already completed.
            current_state: Current state description.
            error: Optional error that triggered replanning.

        Returns:
            Updated plan dictionary.
        """
        messages = [
            LLMMessage(role="system", content=PLANNING_PROMPT),
            LLMMessage(
                role="user",
                content=f"""Original goal: {original_goal}

Completed steps:
{chr(10).join(f'✓ {s}' for s in completed_steps)}

Current state: {current_state}
{f'Error encountered: {error}' if error else ''}

Please create an updated plan for the remaining work.""",
            ),
        ]

        try:
            response = await self.llm.chat(
                messages=messages,
                temperature=0.3,
                max_tokens=1000,
            )
            plan = json.loads(response.content)
            logger.info("plan_updated", remaining_steps=len(plan.get("plan", [])))
            return plan
        except Exception as e:
            logger.error("replanning_failed", error=str(e))
            return {
                "analysis": "Replanning failed, continuing with best effort",
                "plan": [{"step": 1, "task": "Continue working on the goal", "depends_on": []}],
                "estimated_complexity": "unknown",
            }
