"""Skills工具适配器 - 可复用的预定义技能"""

import time
import json
import httpx
from typing import Optional

from app.tools.base import BaseToolAdapter, ToolResult


class SkillsAdapter(BaseToolAdapter):
    """
    技能工具适配器。
    支持三种技能来源：
    - builtin: 系统内置技能（如 web_search, code_review, data_analysis）
    - local: 本地技能包（通过本地模块加载）
    - remote: 远程技能服务（通过HTTP API调用）

    配置格式 (config):
    {
        "skill_id": "web_search",                  # 技能标识
        "source": "builtin",                       # builtin / local / remote
        "skill_url": "http://...",                 # remote模式下的技能服务地址
        "version": "latest",                       # 技能版本
        "timeout": 30,                             # 超时秒数
        "auth": {                                  # 远程技能认证（可选）
            "type": "bearer",
            "token": "xxx"
        },
        "params_mapping": {                        # 参数映射（可选）
            "input": "query"
        }
    }
    """

    # 内置技能注册表
    _builtin_skills = {}

    @classmethod
    def register_builtin(cls, skill_id: str, handler):
        """注册内置技能"""
        cls._builtin_skills[skill_id] = handler

    async def execute(self, config: dict, input_schema: dict, params: dict) -> ToolResult:
        start = time.time()
        source = config.get("source", "builtin")
        skill_id = config.get("skill_id", "")
        timeout = config.get("timeout", 30)

        # 应用参数映射
        mapped_params = self._apply_params_mapping(config, params)

        try:
            if source == "builtin":
                return await self._execute_builtin(skill_id, mapped_params, start)
            elif source == "local":
                return await self._execute_local(skill_id, config, mapped_params, start)
            elif source == "remote":
                return await self._execute_remote(config, mapped_params, start, timeout)
            else:
                return self._timed_result(
                    start, success=False,
                    error=f"不支持的技能来源: {source}，可选: builtin, local, remote"
                )
        except Exception as e:
            return self._timed_result(start, success=False, error=f"技能执行失败: {str(e)}")

    async def _execute_builtin(self, skill_id: str, params: dict, start: float) -> ToolResult:
        """执行内置技能"""
        handler = self._builtin_skills.get(skill_id)
        if not handler:
            available = list(self._builtin_skills.keys()) if self._builtin_skills else ["(暂无内置技能)"]
            return self._timed_result(
                start, success=False,
                error=f"内置技能 '{skill_id}' 不存在，可用技能: {', '.join(available)}"
            )

        try:
            # 支持同步和异步handler
            import asyncio
            if asyncio.iscoroutinefunction(handler):
                result = await handler(params)
            else:
                result = handler(params)

            return self._timed_result(start, success=True, output=result)
        except Exception as e:
            return self._timed_result(start, success=False, error=f"内置技能执行失败: {str(e)}")

    async def _execute_local(self, skill_id: str, config: dict, params: dict, start: float) -> ToolResult:
        """执行本地技能包"""
        try:
            import importlib
            module_path = f"app.skills.{skill_id}"
            module = importlib.import_module(module_path)

            if hasattr(module, "execute"):
                import asyncio
                if asyncio.iscoroutinefunction(module.execute):
                    result = await module.execute(params, config)
                else:
                    result = module.execute(params, config)
                return self._timed_result(start, success=True, output=result)
            else:
                return self._timed_result(
                    start, success=False,
                    error=f"本地技能模块 '{module_path}' 缺少 execute() 函数"
                )
        except ImportError:
            return self._timed_result(
                start, success=False,
                error=f"本地技能模块 'app.skills.{skill_id}' 未找到"
            )
        except Exception as e:
            return self._timed_result(start, success=False, error=f"本地技能执行失败: {str(e)}")

    async def _execute_remote(self, config: dict, params: dict, start: float, timeout: int) -> ToolResult:
        """调用远程技能服务"""
        skill_url = config.get("skill_url", "").rstrip("/")
        if not skill_url:
            return self._timed_result(start, success=False, error="远程技能未配置 skill_url")

        headers = self._build_headers(config)
        skill_id = config.get("skill_id", "")
        version = config.get("version", "latest")

        payload = {
            "skill_id": skill_id,
            "version": version,
            "params": params,
        }

        try:
            async with httpx.AsyncClient(timeout=float(timeout)) as client:
                resp = await client.post(skill_url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                return self._timed_result(start, success=True, output=data)
        except httpx.TimeoutException:
            return self._timed_result(start, success=False, error=f"远程技能调用超时 ({timeout}s)")
        except httpx.HTTPStatusError as e:
            return self._timed_result(
                start, success=False,
                error=f"远程技能返回错误: HTTP {e.response.status_code} - {e.response.text[:200]}"
            )
        except Exception as e:
            return self._timed_result(start, success=False, error=f"远程技能调用失败: {str(e)}")

    async def test_connection(self, config: dict) -> ToolResult:
        start = time.time()
        source = config.get("source", "builtin")
        skill_id = config.get("skill_id", "")

        try:
            if source == "builtin":
                if skill_id in self._builtin_skills:
                    return self._timed_result(
                        start, success=True,
                        output=f"内置技能 '{skill_id}' 已注册，可正常使用"
                    )
                else:
                    available = list(self._builtin_skills.keys()) if self._builtin_skills else ["(暂无)"]
                    return self._timed_result(
                        start, success=False,
                        error=f"内置技能 '{skill_id}' 未注册，可用: {', '.join(available)}"
                    )

            elif source == "local":
                try:
                    import importlib
                    module = importlib.import_module(f"app.skills.{skill_id}")
                    has_execute = hasattr(module, "execute")
                    if has_execute:
                        return self._timed_result(
                            start, success=True,
                            output=f"本地技能 '{skill_id}' 模块已加载，execute() 函数存在"
                        )
                    else:
                        return self._timed_result(
                            start, success=False,
                            error=f"本地技能模块 '{skill_id}' 缺少 execute() 函数"
                        )
                except ImportError:
                    return self._timed_result(
                        start, success=False,
                        error=f"本地技能模块 'app.skills.{skill_id}' 未找到"
                    )

            elif source == "remote":
                skill_url = config.get("skill_url", "").rstrip("/")
                if not skill_url:
                    return self._timed_result(start, success=False, error="未配置 skill_url")

                headers = self._build_headers(config)
                timeout = config.get("timeout", 10)

                async with httpx.AsyncClient(timeout=float(timeout)) as client:
                    # 尝试 GET 请求检查服务可达性
                    resp = await client.get(skill_url, headers=headers)
                    return self._timed_result(
                        start, success=True,
                        output=f"远程技能服务可达 (HTTP {resp.status_code})"
                    )
            else:
                return self._timed_result(start, success=False, error=f"不支持的来源: {source}")

        except Exception as e:
            return self._timed_result(start, success=False, error=f"连通性测试失败: {str(e)}")

    def validate_config(self, config: dict) -> tuple[bool, Optional[str]]:
        skill_id = config.get("skill_id")
        if not skill_id:
            return False, "必须配置 skill_id"

        source = config.get("source", "builtin")
        if source not in ("builtin", "local", "remote"):
            return False, f"不支持的技能来源: {source}，可选: builtin, local, remote"

        if source == "remote":
            skill_url = config.get("skill_url", "")
            if not skill_url:
                return False, "remote 模式必须配置 skill_url"

        return True, None

    def _apply_params_mapping(self, config: dict, params: dict) -> dict:
        """应用参数映射"""
        mapping = config.get("params_mapping")
        if not mapping or not isinstance(mapping, dict):
            return params

        mapped = {}
        for target_key, source_key in mapping.items():
            if source_key in params:
                mapped[target_key] = params[source_key]

        # 保留未映射的原始参数
        for k, v in params.items():
            if k not in mapping.values():
                mapped[k] = v

        return mapped

    def _build_headers(self, config: dict) -> dict:
        """构建请求头"""
        headers = {"Content-Type": "application/json"}
        auth = config.get("auth", {})
        auth_type = auth.get("type", "none")
        token = auth.get("token", "")

        if auth_type == "bearer" and token:
            headers["Authorization"] = f"Bearer {token}"
        elif auth_type == "api_key" and token:
            headers["X-API-Key"] = token

        return headers
