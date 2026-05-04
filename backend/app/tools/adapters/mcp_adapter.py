"""MCP工具适配器 - 通过MCP协议与外部工具服务器通信"""

import time
import httpx
from typing import Optional

from app.tools.base import BaseToolAdapter, ToolResult


class MCPAdapter(BaseToolAdapter):
    """
    MCP (Model Context Protocol) 工具适配器。
    
    配置格式 (config):
    {
        "server_url": "http://localhost:8080",   # MCP服务器地址
        "auth": {                                 # 可选认证
            "type": "bearer",                     # bearer / api_key / basic
            "token": "xxx"
        },
        "timeout": 30                             # 超时秒数
    }
    """

    async def execute(self, config: dict, input_schema: dict, params: dict) -> ToolResult:
        start = time.time()
        server_url = config.get("server_url", "").rstrip("/")
        timeout = config.get("timeout", 30)
        headers = self._build_headers(config)

        try:
            async with httpx.AsyncClient(timeout=float(timeout)) as client:
                resp = await client.post(
                    f"{server_url}/execute",
                    json={"params": params},
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()
                return self._timed_result(
                    start,
                    success=data.get("success", True),
                    output=data.get("result", data),
                    error=data.get("error"),
                )
        except httpx.TimeoutException:
            return self._timed_result(start, success=False, error=f"MCP服务器超时 ({timeout}s)")
        except httpx.HTTPStatusError as e:
            return self._timed_result(start, success=False, error=f"MCP服务器返回错误: {e.response.status_code}")
        except Exception as e:
            return self._timed_result(start, success=False, error=f"MCP执行失败: {str(e)}")

    async def test_connection(self, config: dict) -> ToolResult:
        start = time.time()
        server_url = config.get("server_url", "").rstrip("/")
        timeout = config.get("timeout", 10)
        headers = self._build_headers(config)

        if not server_url:
            return self._timed_result(start, success=False, error="未配置 server_url")

        try:
            async with httpx.AsyncClient(timeout=float(timeout)) as client:
                resp = await client.get(f"{server_url}/health", headers=headers)
                if resp.status_code < 400:
                    return self._timed_result(start, success=True, output="MCP服务器连接正常")
                return self._timed_result(
                    start, success=False,
                    error=f"MCP服务器返回状态码: {resp.status_code}"
                )
        except httpx.ConnectError:
            return self._timed_result(start, success=False, error=f"无法连接到MCP服务器: {server_url}")
        except httpx.TimeoutException:
            return self._timed_result(start, success=False, error=f"MCP服务器连接超时")
        except Exception as e:
            return self._timed_result(start, success=False, error=f"连接测试失败: {str(e)}")

    def validate_config(self, config: dict) -> tuple[bool, Optional[str]]:
        if not config.get("server_url"):
            return False, "缺少必填字段: server_url"
        url = config["server_url"]
        if not url.startswith(("http://", "https://")):
            return False, "server_url 必须以 http:// 或 https:// 开头"
        return True, None

    def _build_headers(self, config: dict) -> dict:
        headers = {"Content-Type": "application/json"}
        auth = config.get("auth")
        if auth:
            auth_type = auth.get("type", "bearer")
            if auth_type == "bearer":
                headers["Authorization"] = f"Bearer {auth.get('token', '')}"
            elif auth_type == "api_key":
                headers[auth.get("header_name", "X-API-Key")] = auth.get("token", "")
            elif auth_type == "basic":
                import base64
                cred = base64.b64encode(
                    f"{auth.get('username', '')}:{auth.get('password', '')}".encode()
                ).decode()
                headers["Authorization"] = f"Basic {cred}"
        return headers

    async def discover_tools(self, config: dict) -> ToolResult:
        """发现MCP服务器上可用的工具列表"""
        start = time.time()
        server_url = config.get("server_url", "").rstrip("/")
        headers = self._build_headers(config)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{server_url}/tools", headers=headers)
                resp.raise_for_status()
                tools = resp.json()
                return self._timed_result(start, success=True, output=tools)
        except Exception as e:
            return self._timed_result(start, success=False, error=f"发现工具失败: {str(e)}")
