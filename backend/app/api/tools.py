"""Tool management API routes - 统一工具管理 CRUD + 执行 + 连通性测试"""

import logging
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.tools.manager import tool_manager
from app.tools.base import AdapterRegistry
from app.api.schemas import (
    ToolCreate, ToolUpdate, ToolOut,
    ToolExecuteRequest, ToolExecuteResponse,
    ToolTestRequest, ToolTestResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tools", tags=["tools"])


# ─── 工具类型 ────────────────────────────────────────────────

@router.get("/types")
async def list_tool_types():
    """获取支持的工具类型列表"""
    type_info = {
        "mcp": {
            "label": "MCP工具",
            "description": "通过MCP协议与外部工具服务器通信",
            "config_fields": [
                {"key": "server_url", "label": "服务器地址", "type": "text", "required": True, "placeholder": "http://localhost:8080"},
                {"key": "auth.type", "label": "认证方式", "type": "select", "options": ["none", "bearer", "api_key", "basic"], "required": False},
                {"key": "auth.token", "label": "认证令牌", "type": "password", "required": False},
                {"key": "timeout", "label": "超时(秒)", "type": "number", "required": False, "default": 30},
            ],
        },
        "api": {
            "label": "API工具",
            "description": "通过HTTP API接口调用外部服务",
            "config_fields": [
                {"key": "endpoint", "label": "API端点", "type": "text", "required": True, "placeholder": "https://api.example.com/v1/action"},
                {"key": "method", "label": "HTTP方法", "type": "select", "options": ["GET", "POST", "PUT", "DELETE", "PATCH"], "required": False, "default": "POST"},
                {"key": "headers", "label": "自定义请求头", "type": "json", "required": False},
                {"key": "auth.type", "label": "认证方式", "type": "select", "options": ["none", "bearer", "api_key", "basic"], "required": False},
                {"key": "auth.token", "label": "认证令牌", "type": "password", "required": False},
                {"key": "timeout", "label": "超时(秒)", "type": "number", "required": False, "default": 30},
                {"key": "response_path", "label": "响应数据路径", "type": "text", "required": False, "placeholder": "data.result"},
            ],
        },
        "agent": {
            "label": "子Agent",
            "description": "将其他Agent作为工具调用",
            "config_fields": [
                {"key": "mode", "label": "模式", "type": "select", "options": ["internal", "external"], "required": True, "default": "internal"},
                {"key": "agent_id", "label": "Agent ID", "type": "text", "required": False, "placeholder": "内部Agent的UUID"},
                {"key": "agent_url", "label": "Agent URL", "type": "text", "required": False, "placeholder": "http://external-agent/api"},
                {"key": "auth.type", "label": "认证方式", "type": "select", "options": ["none", "bearer", "api_key"], "required": False},
                {"key": "auth.token", "label": "认证令牌", "type": "password", "required": False},
                {"key": "timeout", "label": "超时(秒)", "type": "number", "required": False, "default": 60},
            ],
        },
        "script": {
            "label": "本地脚本",
            "description": "执行本地可执行脚本",
            "config_fields": [
                {"key": "script_path", "label": "脚本路径", "type": "text", "required": True, "placeholder": "/path/to/script.py"},
                {"key": "interpreter", "label": "解释器", "type": "select", "options": ["python", "node", "bash", "cmd", "powershell"], "required": False, "default": "python"},
                {"key": "working_dir", "label": "工作目录", "type": "text", "required": False},
                {"key": "args_mode", "label": "参数传递方式", "type": "select", "options": ["json_stdin", "cli_args", "env_vars"], "required": False, "default": "json_stdin"},
                {"key": "timeout", "label": "超时(秒)", "type": "number", "required": False, "default": 30},
                {"key": "env", "label": "环境变量", "type": "json", "required": False},
            ],
        },
        "sandbox": {
            "label": "沙箱代码",
            "description": "在沙箱环境中运行Python代码",
            "config_fields": [
                {"key": "code", "label": "代码模板", "type": "code", "required": False, "placeholder": "def main(params):\n    return params"},
                {"key": "timeout", "label": "超时(秒)", "type": "number", "required": False, "default": 10},
                {"key": "allowed_modules", "label": "允许的模块", "type": "tags", "required": False},
                {"key": "max_output_size", "label": "最大输出(字节)", "type": "number", "required": False, "default": 10000},
            ],
        },
        "skills": {
            "label": "技能工具",
            "description": "可复用的预定义技能，支持本地技能包和远程技能服务",
            "config_fields": [
                {"key": "skill_id", "label": "技能ID", "type": "text", "required": True, "placeholder": "web_search / code_review / data_analysis"},
                {"key": "source", "label": "技能来源", "type": "select", "options": ["builtin", "local", "remote"], "required": True, "default": "builtin"},
                {"key": "skill_url", "label": "远程技能地址", "type": "text", "required": False, "placeholder": "http://skills-server/api/v1/invoke"},
                {"key": "version", "label": "版本", "type": "text", "required": False, "placeholder": "latest"},
                {"key": "auth.type", "label": "认证方式", "type": "select", "options": ["none", "bearer", "api_key"], "required": False},
                {"key": "auth.token", "label": "认证令牌", "type": "password", "required": False},
                {"key": "timeout", "label": "超时(秒)", "type": "number", "required": False, "default": 30},
                {"key": "params_mapping", "label": "参数映射", "type": "json", "required": False, "placeholder": '{"input": "query"}'},
            ],
        },
    }
    available = AdapterRegistry.list_types()
    return {
        "types": {k: v for k, v in type_info.items() if k in available},
        "available": available,
    }


# ─── CRUD ────────────────────────────────────────────────────

@router.get("/", response_model=list[ToolOut])
async def list_tools(
    type: Optional[str] = Query(None, description="按类型筛选"),
    is_active: Optional[bool] = Query(None, description="按状态筛选"),
    db: AsyncSession = Depends(get_db),
):
    """获取工具列表"""
    tools = await tool_manager.list_tools(db, tool_type=type, is_active=is_active)
    return [tool_manager.tool_to_dict(t) for t in tools]


@router.post("/", response_model=ToolOut)
async def create_tool(data: ToolCreate, db: AsyncSession = Depends(get_db)):
    """创建工具"""
    try:
        tool = await tool_manager.create_tool(db, data.model_dump())
        return tool_manager.tool_to_dict(tool)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{tool_id}", response_model=ToolOut)
async def get_tool(tool_id: str, db: AsyncSession = Depends(get_db)):
    """获取单个工具详情"""
    try:
        uid = UUID(tool_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的工具ID")

    tool = await tool_manager.get_tool(db, uid)
    if not tool:
        raise HTTPException(status_code=404, detail="工具不存在")
    return tool_manager.tool_to_dict(tool)


@router.put("/{tool_id}", response_model=ToolOut)
async def update_tool(tool_id: str, data: ToolUpdate, db: AsyncSession = Depends(get_db)):
    """更新工具"""
    try:
        uid = UUID(tool_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的工具ID")

    try:
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        tool = await tool_manager.update_tool(db, uid, update_data)
        if not tool:
            raise HTTPException(status_code=404, detail="工具不存在")
        return tool_manager.tool_to_dict(tool)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{tool_id}")
async def delete_tool(tool_id: str, db: AsyncSession = Depends(get_db)):
    """删除工具"""
    try:
        uid = UUID(tool_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的工具ID")

    success = await tool_manager.delete_tool(db, uid)
    if not success:
        raise HTTPException(status_code=404, detail="工具不存在")
    return {"success": True, "message": "工具已删除"}


# ─── 执行 ────────────────────────────────────────────────────

@router.post("/execute", response_model=ToolExecuteResponse)
async def execute_tool(request: ToolExecuteRequest, db: AsyncSession = Depends(get_db)):
    """执行工具"""
    if request.tool_id:
        try:
            uid = UUID(request.tool_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的工具ID")
        result = await tool_manager.execute_tool(db, uid, request.params, request.context)
    elif request.tool_name:
        result = await tool_manager.execute_tool_by_name(db, request.tool_name, request.params, request.context)
    else:
        raise HTTPException(status_code=400, detail="需要提供 tool_id 或 tool_name")

    return {
        "success": result.success,
        "output": result.output,
        "error": result.error,
        "duration_ms": result.duration_ms,
        "metadata": result.metadata,
    }


# ─── 连通性测试 ──────────────────────────────────────────────

@router.post("/{tool_id}/test", response_model=ToolTestResponse)
async def test_tool_connection(tool_id: str, db: AsyncSession = Depends(get_db)):
    """测试已保存工具的连通性"""
    try:
        uid = UUID(tool_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的工具ID")

    result = await tool_manager.test_connection(db, uid)
    return {
        "success": result.success,
        "message": result.output if result.success else result.error,
        "duration_ms": result.duration_ms,
    }


@router.post("/test-config", response_model=ToolTestResponse)
async def test_tool_config(request: ToolTestRequest):
    """测试工具配置的连通性（无需先创建工具）"""
    result = await tool_manager.test_config(request.type, request.config)
    return {
        "success": result.success,
        "message": result.output if result.success else result.error,
        "duration_ms": result.duration_ms,
    }


# ─── 批量操作 ────────────────────────────────────────────────

@router.post("/batch-test")
async def batch_test_tools(db: AsyncSession = Depends(get_db)):
    """批量测试所有活跃工具的连通性"""
    tools = await tool_manager.list_tools(db, is_active=True)
    results = []
    for tool in tools:
        result = await tool_manager.test_connection(db, tool.id)
        results.append({
            "tool_id": str(tool.id),
            "tool_name": tool.name,
            "type": tool.type.value if hasattr(tool.type, 'value') else tool.type,
            "success": result.success,
            "message": result.output if result.success else result.error,
            "duration_ms": result.duration_ms,
        })
    return {"results": results}


@router.patch("/{tool_id}/toggle")
async def toggle_tool(tool_id: str, db: AsyncSession = Depends(get_db)):
    """切换工具启用/禁用状态"""
    try:
        uid = UUID(tool_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的工具ID")

    tool = await tool_manager.get_tool(db, uid)
    if not tool:
        raise HTTPException(status_code=404, detail="工具不存在")

    updated = await tool_manager.update_tool(db, uid, {"is_active": not tool.is_active})
    return tool_manager.tool_to_dict(updated)
