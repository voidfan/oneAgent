"""File reader tool for reading uploaded documents."""
import os

from app.tools.base import BaseTool, ToolResult


class FileReaderTool(BaseTool):
    """Read content from uploaded files."""

    name = "file_reader"
    description = "Read the content of an uploaded file. Supports text files, CSV, JSON, etc."
    parameters_schema = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to read.",
            },
            "encoding": {
                "type": "string",
                "description": "File encoding.",
                "default": "utf-8",
            },
            "max_lines": {
                "type": "integer",
                "description": "Maximum number of lines to read. 0 for all.",
                "default": 100,
            },
        },
        "required": ["file_path"],
    }

    # Allowed base directories for security
    ALLOWED_DIRS = ["/data/uploads", "/tmp/xagent"]

    async def execute(
        self, file_path: str, encoding: str = "utf-8", max_lines: int = 100, **kwargs
    ) -> ToolResult:
        # Security: only allow reading from specific directories
        abs_path = os.path.abspath(file_path)
        if not any(abs_path.startswith(d) for d in self.ALLOWED_DIRS):
            return ToolResult(
                success=False,
                error=f"Access denied. File must be in one of: {self.ALLOWED_DIRS}",
            )

        if not os.path.exists(abs_path):
            return ToolResult(success=False, error=f"File not found: {file_path}")

        try:
            with open(abs_path, "r", encoding=encoding) as f:
                if max_lines > 0:
                    lines = []
                    for i, line in enumerate(f):
                        if i >= max_lines:
                            lines.append(f"\n... (truncated at {max_lines} lines)")
                            break
                        lines.append(line)
                    content = "".join(lines)
                else:
                    content = f.read()

            return ToolResult(
                success=True,
                output={
                    "file_path": file_path,
                    "content": content,
                    "size_bytes": os.path.getsize(abs_path),
                },
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to read file: {str(e)}")
