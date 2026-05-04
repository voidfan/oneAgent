"""Agent工具适配器 - 将子Agent作为工具调用"""

import time
import httpx
from typing import Optional

from app.tools.base import BaseToolAdapter, ToolResult


class AgentAdapter(BaseToolAdapter):
    """
    子Agent工具适配器。
    将其他Agent作为工具来调用，通过API接口与Agent通信。
    
    配置格式 (config):
    {
        "agent_id": "uuid-of-agent",             # 本系统内的Agent ID
        "agent_url": "http://...",                # 或外部Agent的API地址
        "mode": "internal",                       # internal（本系统Agent）/ external（外部Agent API）
        "timeout": 60,                            # 超时秒数
        "auth": {                                 # 外部Agent认证（可选）
            "type": "bearer",
            "token": "xxx"
        }
    }
    """

    async def execute(self, config: dict, input_schema: dict, params: dict) -> ToolResult:
        start = time.time()
        mode = config.get("mode", "internal")
        timeout = config.get("timeout", 60)

        try:
            if mode == "internal":
                return await self._execute_internal(config, params, start, timeout)
            else:
                return await self._execute_external(config, params, start, timeout)
        except Exception as e:
            return self._timed_result(start, success=False, error=f"Agent调用失败: {str(e)}")

    async def _execute_internal(self, config: dict, params: dict, start: float, timeout: int) -> ToolResult:
        """调用本系统内部的Agent"""
        agent_id = config.get("agent_id")
        if not agent_id:
            return self._timed_result(start, success=False, error="未配置 agent_id")

        # 通过内部API调用Agent
        try:
            async with httpx.AsyncClient(timeout=float(timeout)) as client:
                resp = await client.post(
                    f"http://localhost:8000/api/chat/",
                    json={
                        "message": params.get("message", str(params)),
                        "agent_id": agent_id,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return self._timed_result(
                    start, success=True,
                    output=data.get("response", data)
                )
        except Exception as e:
            return self._timed_result(start, success=False, error=f"内部Agent调用失败: {str(e)}")

    async def _execute_external(self, config: dict, params: dict, start: float, timeout: int) -> ToolResult:
        """调用外部Agent API"""
        agent_url = config.get("agent_url", "").rstrip("/")
        headers = self._build_headers(config)

        try:
            async with httpx.AsyncClient(timeout=float(timeout)) as client:
                resp = await client.post(
                    agent_url,
                    json=params,
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()
                return self._timed_result(start, success=True, output=data)
        except httpx.TimeoutException:
            return self._timed_result(start, success=False, error=f"外部Agent超时 ({timeout}s)")
        except Exception as e:
            return self._timed_result(start, success=False, error=f"外部Agent调用失败: {str(e)}")

    async def test_connection(self, config: dict) -> ToolResult:
        start = time.time()
        mode = config.get("mode", "internal")

        if mode == "internal":
            agent_id = config.get("agent_id")
            if not agent_id:
                return self._timed_result(start, success=False, error="未配置 agent_id")
            # 检查Agent是否存在
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(f"http://localhost:8000/api/agents/{agent_id}")
                    if resp.status_code == 200:
                        return self._timed_result(start, success=True, output="内部Agent连接正常")
                    return self._timed_result(
                        start, success=False,
                        error=f"Agent不存在或不可用 (状态码: {resp.status_code})"
                    )
            except Exception as e:
                return self._timed_result(start, success=False, error=f"Agent连接测试失败: {str(e)}")
        else:
            agent_url = config.get("agent_url", "").rstrip("/")
            if not agent_url:
                return self._timed_result(start, success=False, error="未配置 agent_url")
            try:
                headers = self._build_headers(config)
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(agent_url, headers=headers)
                    if resp.status_code < 500:
                        return self._timed_result(start, success=True, output="外部Agent连接正常")
                    return self._timed_result(
                        start, success=False,
                        error=f"外部Agent服务器错误: {resp.status_code}"
                    )
            except httpx.ConnectError:
                return self._timed_result(start, success=False, error=f"无法连接到Agent: {agent_url}")
            except Exception as e:
                return self._timed_result(start, success=False, error=f"连接测试失败: {str(e)}")

    def validate_config(self, config: dict) -> tuple[bool, Optional[str]]:
        mode = config.get("mode", "internal")
        if mode == "internal":
            if not config.get("agent_id"):
                return False, "内部模式需要配置 agent_id"
        elif mode == "external":
            if not config.get("agent_url"):
                return False, "外部模式需要配置 agent_url"
            url = config["agent_url"]
            if not url.startswith(("http://", "https://")):
                return False, "agent_url 必须以 http:// 或 https:// 开头"
        else:
            return False, f"不支持的模式: {mode}，请使用 internal 或 external"
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
        return headers
