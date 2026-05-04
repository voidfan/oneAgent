"""Base tool interface, result dataclass, and adapter registry."""

import time
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional, Dict, List


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    output: Any = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
        }

    def to_str(self) -> str:
        if self.success:
            return json.dumps(self.output) if not isinstance(self.output, str) else self.output
        return f"Error: {self.error}"


class BaseToolAdapter(ABC):
    """
    工具适配器基类。
    每种工具类型（MCP、API、Agent、Script、Sandbox）都有对应的适配器。
    适配器负责：执行工具、测试连通性、验证配置。
    """

    @abstractmethod
    async def execute(self, config: dict, input_schema: dict, params: dict) -> ToolResult:
        """
        执行工具。
        
        Args:
            config: 工具配置（来自 Tool.config）
            input_schema: 工具输入 schema
            params: 实际调用参数
        Returns:
            ToolResult
        """
        ...

    @abstractmethod
    async def test_connection(self, config: dict) -> ToolResult:
        """
        测试工具连通性。
        
        Args:
            config: 工具配置
        Returns:
            ToolResult (success=True 表示连通)
        """
        ...

    @abstractmethod
    def validate_config(self, config: dict) -> tuple[bool, Optional[str]]:
        """
        验证工具配置是否合法。
        
        Args:
            config: 工具配置
        Returns:
            (is_valid, error_message)
        """
        ...

    def _timed_result(self, start: float, **kwargs) -> ToolResult:
        """创建带耗时的 ToolResult"""
        elapsed = (time.time() - start) * 1000
        return ToolResult(duration_ms=round(elapsed, 2), **kwargs)


class AdapterRegistry:
    """适配器注册表 - 管理所有工具类型的适配器"""

    _adapters: Dict[str, BaseToolAdapter] = {}

    @classmethod
    def register(cls, tool_type: str, adapter: BaseToolAdapter) -> None:
        cls._adapters[tool_type] = adapter

    @classmethod
    def get(cls, tool_type: str) -> Optional[BaseToolAdapter]:
        return cls._adapters.get(tool_type)

    @classmethod
    def list_types(cls) -> List[str]:
        return list(cls._adapters.keys())

    @classmethod
    def has(cls, tool_type: str) -> bool:
        return tool_type in cls._adapters
