"""Sandbox工具适配器 - 在沙箱环境中运行代码"""

import time
import asyncio
import json
import sys
import io
from typing import Optional

from app.tools.base import BaseToolAdapter, ToolResult


class SandboxAdapter(BaseToolAdapter):
    """
    沙箱代码执行工具适配器。
    在受限环境中运行Python代码。
    
    配置格式 (config):
    {
        "code": "def main(params):\\n    return ...",  # 预定义代码模板
        "timeout": 10,                                 # 超时秒数
        "allowed_modules": ["json", "math", "re"],     # 允许导入的模块
        "max_output_size": 10000                        # 最大输出字节数
    }
    """

    # 默认允许的模块
    DEFAULT_ALLOWED_MODULES = {
        "json", "math", "re", "datetime", "collections",
        "itertools", "functools", "operator", "string",
        "hashlib", "base64", "urllib.parse", "decimal",
        "statistics", "random", "uuid", "copy",
    }

    # 禁止的内置函数/属性
    BLOCKED_BUILTINS = {
        "exec", "eval", "compile", "__import__",
        "open", "input", "breakpoint",
    }

    async def execute(self, config: dict, input_schema: dict, params: dict) -> ToolResult:
        start = time.time()
        code = config.get("code", "")
        timeout = config.get("timeout", 10)
        allowed_modules = set(config.get("allowed_modules", [])) | self.DEFAULT_ALLOWED_MODULES
        max_output = config.get("max_output_size", 10000)

        if not code:
            # 如果没有预定义代码，从参数中获取
            code = params.pop("code", "")

        if not code:
            return self._timed_result(start, success=False, error="没有可执行的代码")

        try:
            result = await self._run_sandboxed(code, params, timeout, allowed_modules, max_output)
            return self._timed_result(start, **result)
        except Exception as e:
            return self._timed_result(start, success=False, error=f"沙箱执行失败: {str(e)}")

    async def _run_sandboxed(
        self, code: str, params: dict, timeout: int,
        allowed_modules: set, max_output: int
    ) -> dict:
        """在沙箱中运行代码"""

        # 安全检查
        is_safe, error = self._check_code_safety(code)
        if not is_safe:
            return {"success": False, "error": f"代码安全检查失败: {error}"}

        # 创建受限的全局命名空间
        safe_builtins = {
            k: v for k, v in __builtins__.items()
            if k not in self.BLOCKED_BUILTINS
        } if isinstance(__builtins__, dict) else {
            k: getattr(__builtins__, k)
            for k in dir(__builtins__)
            if k not in self.BLOCKED_BUILTINS and not k.startswith("_")
        }

        # 安全的 import 函数
        def safe_import(name, *args, **kwargs):
            if name.split(".")[0] not in allowed_modules:
                raise ImportError(f"不允许导入模块: {name}")
            return __import__(name, *args, **kwargs)

        safe_builtins["__import__"] = safe_import

        sandbox_globals = {
            "__builtins__": safe_builtins,
            "params": params,
            "json": __import__("json"),
            "math": __import__("math"),
            "re": __import__("re"),
        }

        # 捕获stdout
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        captured_stdout = io.StringIO()
        captured_stderr = io.StringIO()

        def _exec():
            sys.stdout = captured_stdout
            sys.stderr = captured_stderr
            try:
                compiled = compile(code, "<sandbox>", "exec")
                exec(compiled, sandbox_globals)

                # 检查是否有 main 函数
                if "main" in sandbox_globals and callable(sandbox_globals["main"]):
                    return sandbox_globals["main"](params)

                # 检查是否有 result 变量
                if "result" in sandbox_globals:
                    return sandbox_globals["result"]

                # 返回stdout输出
                output = captured_stdout.getvalue()
                return output if output else None
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

        try:
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(None, _exec),
                timeout=timeout,
            )

            # 限制输出大小
            if isinstance(result, str) and len(result) > max_output:
                result = result[:max_output] + f"\n... (输出被截断，超过 {max_output} 字节)"

            stdout_val = captured_stdout.getvalue()
            stderr_val = captured_stderr.getvalue()

            metadata = {}
            if stdout_val:
                metadata["stdout"] = stdout_val[:max_output]
            if stderr_val:
                metadata["stderr"] = stderr_val[:max_output]

            return {"success": True, "output": result, "metadata": metadata}

        except asyncio.TimeoutError:
            return {"success": False, "error": f"代码执行超时 ({timeout}s)"}
        except Exception as e:
            return {"success": False, "error": f"执行错误: {type(e).__name__}: {str(e)}"}

    def _check_code_safety(self, code: str) -> tuple[bool, Optional[str]]:
        """基本的代码安全检查"""
        dangerous_patterns = [
            ("os.system", "禁止调用系统命令"),
            ("subprocess", "禁止使用subprocess"),
            ("shutil.rmtree", "禁止删除目录"),
            ("__class__", "禁止访问类元信息"),
            ("__subclasses__", "禁止访问子类"),
            ("globals()", "禁止访问全局变量"),
            ("locals()", "禁止访问局部变量"),
        ]
        for pattern, msg in dangerous_patterns:
            if pattern in code:
                return False, msg
        return True, None

    async def test_connection(self, config: dict) -> ToolResult:
        """测试沙箱环境是否正常"""
        start = time.time()

        try:
            # 运行一个简单的测试代码
            test_result = await self._run_sandboxed(
                code="result = 'sandbox_ok'",
                params={},
                timeout=5,
                allowed_modules=self.DEFAULT_ALLOWED_MODULES,
                max_output=1000,
            )

            if test_result.get("success") and test_result.get("output") == "sandbox_ok":
                return self._timed_result(start, success=True, output="沙箱环境正常")
            return self._timed_result(
                start, success=False,
                error=f"沙箱测试失败: {test_result.get('error', '未知错误')}"
            )
        except Exception as e:
            return self._timed_result(start, success=False, error=f"沙箱测试失败: {str(e)}")

    def validate_config(self, config: dict) -> tuple[bool, Optional[str]]:
        code = config.get("code", "")
        if code:
            is_safe, error = self._check_code_safety(code)
            if not is_safe:
                return False, f"代码安全检查失败: {error}"
            # 尝试编译检查语法
            try:
                compile(code, "<validate>", "exec")
            except SyntaxError as e:
                return False, f"代码语法错误: {str(e)}"

        timeout = config.get("timeout", 10)
        if not isinstance(timeout, (int, float)) or timeout <= 0 or timeout > 300:
            return False, "timeout 必须在 1-300 秒之间"

        return True, None
