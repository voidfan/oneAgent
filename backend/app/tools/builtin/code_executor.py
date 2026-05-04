"""Code executor tool - runs Python code in a restricted environment."""
import asyncio
import io
import sys
from contextlib import redirect_stdout, redirect_stderr

from app.tools.base import BaseTool, ToolResult


class CodeExecutorTool(BaseTool):
    """Execute Python code in a sandboxed environment."""

    name = "code_executor"
    description = "Execute Python code and return the output. Only safe operations are allowed."
    requires_approval = True  # Requires human approval for safety
    parameters_schema = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Python code to execute.",
            },
            "timeout": {
                "type": "integer",
                "description": "Execution timeout in seconds.",
                "default": 10,
            },
        },
        "required": ["code"],
    }

    # Blocked modules/builtins for safety
    BLOCKED_IMPORTS = {
        "os", "sys", "subprocess", "shutil", "pathlib",
        "socket", "http", "urllib", "requests", "ctypes",
        "importlib", "pickle", "shelve", "signal",
    }

    def _check_code_safety(self, code: str) -> tuple[bool, str]:
        """Basic static check for dangerous operations."""
        import ast
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, f"Syntax error: {e}"

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name.split(".")[0]
                    if module in self.BLOCKED_IMPORTS:
                        return False, f"Import of '{module}' is not allowed"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module = node.module.split(".")[0]
                    if module in self.BLOCKED_IMPORTS:
                        return False, f"Import from '{module}' is not allowed"

        return True, ""

    async def execute(self, code: str, timeout: int = 10, **kwargs) -> ToolResult:
        # Safety check
        is_safe, error = self._check_code_safety(code)
        if not is_safe:
            return ToolResult(success=False, error=f"Code safety check failed: {error}")

        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        # Restricted globals
        safe_globals = {
            "__builtins__": {
                "print": print,
                "len": len,
                "range": range,
                "enumerate": enumerate,
                "zip": zip,
                "map": map,
                "filter": filter,
                "sorted": sorted,
                "reversed": reversed,
                "list": list,
                "dict": dict,
                "set": set,
                "tuple": tuple,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "abs": abs,
                "round": round,
                "min": min,
                "max": max,
                "sum": sum,
                "any": any,
                "all": all,
                "isinstance": isinstance,
                "type": type,
                "hasattr": hasattr,
                "getattr": getattr,
            }
        }

        def _run():
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(code, safe_globals)

        try:
            loop = asyncio.get_event_loop()
            await asyncio.wait_for(
                loop.run_in_executor(None, _run),
                timeout=timeout,
            )

            stdout_val = stdout_capture.getvalue()
            stderr_val = stderr_capture.getvalue()

            output = ""
            if stdout_val:
                output += stdout_val
            if stderr_val:
                output += f"\n[stderr]: {stderr_val}"

            return ToolResult(
                success=True,
                output=output.strip() if output.strip() else "(no output)",
            )
        except asyncio.TimeoutError:
            return ToolResult(success=False, error=f"Code execution timed out after {timeout}s")
        except Exception as e:
            return ToolResult(success=False, error=f"Execution error: {str(e)}")
