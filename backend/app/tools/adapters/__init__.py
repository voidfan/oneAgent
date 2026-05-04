"""工具适配器模块 - 注册所有工具类型的适配器"""

from app.tools.base import AdapterRegistry
from app.tools.adapters.mcp_adapter import MCPAdapter
from app.tools.adapters.api_adapter import APIAdapter
from app.tools.adapters.agent_adapter import AgentAdapter
from app.tools.adapters.script_adapter import ScriptAdapter
from app.tools.adapters.sandbox_adapter import SandboxAdapter
from app.tools.adapters.skills_adapter import SkillsAdapter


def register_adapters():
    """注册所有工具适配器"""
    AdapterRegistry.register("mcp", MCPAdapter())
    AdapterRegistry.register("api", APIAdapter())
    AdapterRegistry.register("agent", AgentAdapter())
    AdapterRegistry.register("script", ScriptAdapter())
    AdapterRegistry.register("sandbox", SandboxAdapter())
    AdapterRegistry.register("skills", SkillsAdapter())


__all__ = [
    "MCPAdapter",
    "APIAdapter",
    "AgentAdapter",
    "ScriptAdapter",
    "SandboxAdapter",
    "SkillsAdapter",
    "register_adapters",
]
