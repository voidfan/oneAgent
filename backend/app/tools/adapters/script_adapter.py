"""Script工具适配器 - 执行本地脚本"""

import os
import time
import asyncio
import json
from typing import Optional

from app.tools.base import BaseToolAdapter, ToolResult


class ScriptAdapter(BaseToolAdapter):
    """
    本地脚本工具适配器。
    执行本地可执行脚本（Python、Shell、Node.js等）。
    
    配置格式 (config):
    {
        "script_path": "/path/to/script.py",     # 脚本路径
        "interpreter": "python",                  # 解释器: python / node / bash / cmd / powershell
        "working_dir": "/path/to/workdir",        # 工作目录（可选）
        "timeout": 30,                            # 超时秒数
        "env": {"KEY": "VALUE"},                  # 环境变量（可选）
        "args_mode": "json_stdin"                 # 参数传递方式: json_stdin / cli_args / env_vars
    }
    """

    # 允许的解释器白名单
    ALLOWED_INTERPRETERS = {
        "python": ["python", "python3"],
        "node": ["node", "nodejs"],
        "bash": ["bash", "sh"],
        "cmd": ["cmd"],
        "powershell": ["powershell", "pwsh"],
    }

    async def execute(self, config: dict, input_schema: dict, params: dict) -> ToolResult:
        start = time.time()
        script_path = config.get("script_path", "")
        interpreter = config.get("interpreter", "python")
        timeout = config.get("timeout", 30)
        working_dir = config.get("working_dir")
        env_vars = config.get("env", {})
        args_mode = config.get("args_mode", "json_stdin")

        # 验证脚本存在
        if not os.path.isfile(script_path):
            return self._timed_result(start, success=False, error=f"脚本文件不存在: {script_path}")

        try:
            # 构建命令
            cmd = self._build_command(interpreter, script_path, args_mode, params)

            # 准备环境变量
            env = os.environ.copy()
            env.update(env_vars)
            if args_mode == "env_vars":
                for k, v in params.items():
                    env[f"TOOL_PARAM_{k.upper()}"] = str(v)

            # 准备stdin
            stdin_data = None
            if args_mode == "json_stdin":
                stdin_data = json.dumps(params).encode("utf-8")

            # 执行脚本
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE if stdin_data else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
                env=env,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(input=stdin_data),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return self._timed_result(start, success=False, error=f"脚本执行超时 ({timeout}s)")

            stdout_str = stdout.decode("utf-8", errors="replace").strip()
            stderr_str = stderr.decode("utf-8", errors="replace").strip()

            if process.returncode == 0:
                # 尝试解析JSON输出
                try:
                    output = json.loads(stdout_str)
                except (json.JSONDecodeError, ValueError):
                    output = stdout_str

                return self._timed_result(
                    start, success=True, output=output,
                    metadata={"stderr": stderr_str} if stderr_str else {},
                )
            else:
                return self._timed_result(
                    start, success=False,
                    error=f"脚本退出码 {process.returncode}: {stderr_str or stdout_str}",
                )

        except Exception as e:
            return self._timed_result(start, success=False, error=f"脚本执行失败: {str(e)}")

    async def test_connection(self, config: dict) -> ToolResult:
        start = time.time()
        script_path = config.get("script_path", "")
        interpreter = config.get("interpreter", "python")

        if not script_path:
            return self._timed_result(start, success=False, error="未配置 script_path")

        # 检查脚本文件是否存在
        if not os.path.isfile(script_path):
            return self._timed_result(start, success=False, error=f"脚本文件不存在: {script_path}")

        # 检查解释器是否可用
        interpreter_cmd = self._get_interpreter_cmd(interpreter)
        if not interpreter_cmd:
            return self._timed_result(start, success=False, error=f"不支持的解释器: {interpreter}")

        try:
            process = await asyncio.create_subprocess_exec(
                interpreter_cmd, "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=5)
            version = (stdout or stderr).decode("utf-8", errors="replace").strip()

            if process.returncode == 0:
                return self._timed_result(
                    start, success=True,
                    output=f"脚本就绪 (解释器: {interpreter_cmd}, 版本: {version})"
                )
            return self._timed_result(start, success=False, error=f"解释器不可用: {interpreter_cmd}")
        except FileNotFoundError:
            return self._timed_result(start, success=False, error=f"解释器未找到: {interpreter_cmd}")
        except Exception as e:
            return self._timed_result(start, success=False, error=f"连接测试失败: {str(e)}")

    def validate_config(self, config: dict) -> tuple[bool, Optional[str]]:
        if not config.get("script_path"):
            return False, "缺少必填字段: script_path"
        interpreter = config.get("interpreter", "python")
        if interpreter not in self.ALLOWED_INTERPRETERS:
            return False, f"不支持的解释器: {interpreter}，支持: {list(self.ALLOWED_INTERPRETERS.keys())}"
        args_mode = config.get("args_mode", "json_stdin")
        if args_mode not in ("json_stdin", "cli_args", "env_vars"):
            return False, f"不支持的参数传递方式: {args_mode}"
        return True, None

    def _get_interpreter_cmd(self, interpreter: str) -> Optional[str]:
        """获取解释器命令"""
        cmds = self.ALLOWED_INTERPRETERS.get(interpreter, [])
        return cmds[0] if cmds else None

    def _build_command(self, interpreter: str, script_path: str, args_mode: str, params: dict) -> list:
        """构建执行命令"""
        cmd_name = self._get_interpreter_cmd(interpreter)
        cmd = [cmd_name, script_path]

        if args_mode == "cli_args":
            for k, v in params.items():
                cmd.extend([f"--{k}", str(v)])

        return cmd
