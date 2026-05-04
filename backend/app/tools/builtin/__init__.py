"""Built-in tools."""
from app.tools.builtin.web_search import WebSearchTool
from app.tools.builtin.calculator import CalculatorTool
from app.tools.builtin.code_executor import CodeExecutorTool
from app.tools.builtin.file_reader import FileReaderTool
from app.tools.base import tool_registry


def register_builtin_tools():
    """Register all built-in tools."""
    tool_registry.register(WebSearchTool())
    tool_registry.register(CalculatorTool())
    tool_registry.register(CodeExecutorTool())
    tool_registry.register(FileReaderTool())


__all__ = [
    "WebSearchTool",
    "CalculatorTool",
    "CodeExecutorTool",
    "FileReaderTool",
    "register_builtin_tools",
]
