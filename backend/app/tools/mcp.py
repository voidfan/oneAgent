"""MCP (Model Context Protocol) support for tool integration."""
import json
from typing import Any, Optional

import httpx
import structlog

from app.tools.base import BaseTool, ToolResult, tool_registry

logger = structlog.get_logger(__name__)


class MCPToolProxy(BaseTool):
    """Proxy tool that forwards execution to an MCP server."""

    def __init__(
        self,
        name: str,
        description: str,
        parameters_schema: dict,
        server_url: str,
        requires_approval: bool = False,
    ):
        self.name = name
        self.description = description
        self.parameters_schema = parameters_schema
        self.server_url = server_url
        self.requires_approval = requires_approval

    async def execute(self, **kwargs) -> ToolResult:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.server_url}/tools/{self.name}/execute",
                    json={"arguments": kwargs},
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                data = response.json()

                if data.get("error"):
                    return ToolResult(success=False, error=data["error"])
                return ToolResult(success=True, output=data.get("result"))
        except httpx.HTTPStatusError as e:
            return ToolResult(success=False, error=f"MCP server error: {e.response.status_code}")
        except Exception as e:
            return ToolResult(success=False, error=f"MCP call failed: {str(e)}")


class MCPClient:
    """Client for discovering and registering tools from MCP servers."""

    def __init__(self, server_url: str):
        self.server_url = server_url.rstrip("/")

    async def discover_tools(self) -> list[dict]:
        """Discover available tools from the MCP server."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.server_url}/tools")
                response.raise_for_status()
                data = response.json()
                return data.get("tools", [])
        except Exception as e:
            logger.error("mcp_discovery_failed", server=self.server_url, error=str(e))
            return []

    async def register_tools(self) -> list[str]:
        """Discover and register all tools from the MCP server."""
        tools_data = await self.discover_tools()
        registered = []

        for tool_data in tools_data:
            name = tool_data.get("name")
            if not name:
                continue

            proxy = MCPToolProxy(
                name=name,
                description=tool_data.get("description", ""),
                parameters_schema=tool_data.get("input_schema", {}),
                server_url=self.server_url,
                requires_approval=tool_data.get("requires_approval", False),
            )
            tool_registry.register(proxy)
            registered.append(name)
            logger.info("mcp_tool_registered", tool=name, server=self.server_url)

        return registered

    async def health_check(self) -> bool:
        """Check if the MCP server is healthy."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.server_url}/health")
                return response.status_code == 200
        except Exception:
            return False
