"""Tool execution sandbox for security isolation."""
import asyncio
import time
from typing import Any, Optional

import structlog

from app.config import settings
from app.tools.base import BaseTool, ToolResult

logger = structlog.get_logger(__name__)


class ToolSandbox:
    """Sandbox for safe tool execution with timeout and permission control."""

    def __init__(
        self,
        timeout_seconds: int = 30,
        allowed_modules: Optional[list[str]] = None,
    ):
        self.timeout_seconds = timeout_seconds
        self.allowed_modules = allowed_modules or settings.ALLOWED_TOOL_MODULES

    def is_tool_allowed(self, tool: BaseTool) -> bool:
        """Check if a tool is allowed to execute."""
        if not settings.TOOL_SANDBOX_ENABLED:
            return True
        module = tool.__class__.__module__
        return any(module.startswith(allowed) for allowed in self.allowed_modules)

    async def execute(self, tool: BaseTool, params: dict) -> ToolResult:
        """Execute a tool within the sandbox."""
        if not self.is_tool_allowed(tool):
            return ToolResult(
                success=False,
                error=f"Tool '{tool.name}' is not allowed in sandbox. Module: {tool.__class__.__module__}",
            )

        # Validate parameters
        is_valid, error = tool.validate_params(params)
        if not is_valid:
            return ToolResult(success=False, error=f"Parameter validation failed: {error}")

        start_time = time.monotonic()
        try:
            result = await asyncio.wait_for(
                tool.execute(**params),
                timeout=self.timeout_seconds,
            )
            duration_ms = int((time.monotonic() - start_time) * 1000)
            logger.info(
                "tool_executed",
                tool=tool.name,
                success=result.success,
                duration_ms=duration_ms,
            )
            return result
        except asyncio.TimeoutError:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            logger.warning(
                "tool_timeout",
                tool=tool.name,
                timeout=self.timeout_seconds,
                duration_ms=duration_ms,
            )
            return ToolResult(
                success=False,
                error=f"Tool '{tool.name}' timed out after {self.timeout_seconds}s",
            )
        except Exception as e:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            logger.error(
                "tool_error",
                tool=tool.name,
                error=str(e),
                duration_ms=duration_ms,
            )
            return ToolResult(success=False, error=str(e))
