"""API工具适配器 - 通过HTTP API接口调用外部服务"""

import time
import json
import httpx
from typing import Optional

from app.tools.base import BaseToolAdapter, ToolResult


class APIAdapter(BaseToolAdapter):
    """
    HTTP API 工具适配器。
    
    配置格式 (config):
    {
        "endpoint": "https://api.example.com/v1/action",
        "method": "POST",                        # GET / POST / PUT / DELETE
        "headers": {"X-Custom": "value"},         # 自定义请求头
        "auth": {                                 # 可选认证
            "type": "bearer",                     # bearer / api_key / basic
            "token": "xxx"
        },
        "timeout": 30,                            # 超时秒数
        "response_path": "data.result",           # 从响应JSON中提取结果的路径
        "param_mapping": {                        # 参数映射（可选）
            "query": ["q"],                       # 放入query string的参数
            "body": ["*"],                        # 放入body的参数（* 表示全部）
            "path": []                            # 放入URL路径的参数
        }
    }
    """

    async def execute(self, config: dict, input_schema: dict, params: dict) -> ToolResult:
        start = time.time()
        endpoint = config.get("endpoint", "")
        method = config.get("method", "POST").upper()
        timeout = config.get("timeout", 30)
        headers = self._build_headers(config)
        response_path = config.get("response_path")

        try:
            # 处理路径参数
            url = self._build_url(endpoint, config, params)
            query_params, body_params = self._split_params(config, params)

            async with httpx.AsyncClient(timeout=float(timeout)) as client:
                resp = await client.request(
                    method,
                    url,
                    params=query_params if query_params else None,
                    json=body_params if method in ("POST", "PUT", "PATCH") and body_params else None,
                    headers=headers,
                )
                resp.raise_for_status()

                # 尝试解析JSON
                try:
                    data = resp.json()
                except Exception:
                    data = resp.text

                # 提取指定路径的结果
                if response_path and isinstance(data, dict):
                    data = self._extract_path(data, response_path)

                return self._timed_result(start, success=True, output=data)

        except httpx.TimeoutException:
            return self._timed_result(start, success=False, error=f"API请求超时 ({timeout}s)")
        except httpx.HTTPStatusError as e:
            error_body = ""
            try:
                error_body = e.response.text[:500]
            except Exception:
                pass
            return self._timed_result(
                start, success=False,
                error=f"API返回错误 {e.response.status_code}: {error_body}"
            )
        except Exception as e:
            return self._timed_result(start, success=False, error=f"API调用失败: {str(e)}")

    async def test_connection(self, config: dict) -> ToolResult:
        start = time.time()
        endpoint = config.get("endpoint", "")
        timeout = min(config.get("timeout", 10), 15)
        headers = self._build_headers(config)

        if not endpoint:
            return self._timed_result(start, success=False, error="未配置 endpoint")

        try:
            # 对API端点发送HEAD或GET请求测试连通性
            async with httpx.AsyncClient(timeout=float(timeout)) as client:
                # 先尝试HEAD
                try:
                    resp = await client.head(endpoint, headers=headers)
                except Exception:
                    resp = await client.get(endpoint, headers=headers)

                if resp.status_code < 500:
                    return self._timed_result(
                        start, success=True,
                        output=f"API连接正常 (状态码: {resp.status_code})"
                    )
                return self._timed_result(
                    start, success=False,
                    error=f"API服务器错误: {resp.status_code}"
                )
        except httpx.ConnectError:
            return self._timed_result(start, success=False, error=f"无法连接到API: {endpoint}")
        except httpx.TimeoutException:
            return self._timed_result(start, success=False, error="API连接超时")
        except Exception as e:
            return self._timed_result(start, success=False, error=f"连接测试失败: {str(e)}")

    def validate_config(self, config: dict) -> tuple[bool, Optional[str]]:
        if not config.get("endpoint"):
            return False, "缺少必填字段: endpoint"
        endpoint = config["endpoint"]
        if not endpoint.startswith(("http://", "https://")):
            return False, "endpoint 必须以 http:// 或 https:// 开头"
        method = config.get("method", "POST").upper()
        if method not in ("GET", "POST", "PUT", "DELETE", "PATCH"):
            return False, f"不支持的HTTP方法: {method}"
        return True, None

    def _build_headers(self, config: dict) -> dict:
        headers = {"Content-Type": "application/json"}
        custom_headers = config.get("headers", {})
        if custom_headers:
            headers.update(custom_headers)

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

    def _build_url(self, endpoint: str, config: dict, params: dict) -> str:
        """替换URL中的路径参数"""
        mapping = config.get("param_mapping", {})
        path_params = mapping.get("path", [])
        url = endpoint
        for p in path_params:
            if p in params:
                url = url.replace(f"{{{p}}}", str(params[p]))
        return url

    def _split_params(self, config: dict, params: dict) -> tuple[dict, dict]:
        """根据映射拆分参数为query和body"""
        mapping = config.get("param_mapping", {})
        query_keys = set(mapping.get("query", []))
        body_keys = set(mapping.get("body", []))
        path_keys = set(mapping.get("path", []))

        # 如果没有映射配置，全部放入body
        if not mapping or (not query_keys and not body_keys):
            return {}, params

        query = {}
        body = {}
        for k, v in params.items():
            if k in path_keys:
                continue
            if k in query_keys:
                query[k] = v
            elif "*" in body_keys or k in body_keys:
                body[k] = v
            else:
                body[k] = v

        return query, body

    def _extract_path(self, data: dict, path: str):
        """从嵌套字典中按路径提取值"""
        keys = path.split(".")
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return data  # 路径不存在则返回原始数据
        return current
