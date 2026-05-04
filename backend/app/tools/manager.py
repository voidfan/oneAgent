"""统一工具管理器 - 基于数据库持久化和适配器模式"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tool import Tool, ToolType, ToolExecution
from app.tools.base import AdapterRegistry, ToolResult, BaseToolAdapter

logger = logging.getLogger(__name__)


class ToolManager:
    """
    统一工具管理器。
    
    职责：
    - CRUD 操作（通过数据库持久化）
    - 工具执行（通过适配器分发）
    - 连通性测试
    - 执行记录
    - OpenAI function calling schema 生成
    """

    # ─── CRUD ────────────────────────────────────────────────

    async def create_tool(self, db: AsyncSession, data: dict) -> Tool:
        """创建工具"""
        tool_type = data.get("type")

        # 验证适配器是否存在
        adapter = AdapterRegistry.get(tool_type)
        if not adapter:
            raise ValueError(f"不支持的工具类型: {tool_type}")

        # 验证配置
        config = data.get("config", {})
        is_valid, error = adapter.validate_config(config)
        if not is_valid:
            raise ValueError(f"配置验证失败: {error}")

        tool = Tool(
            name=data["name"],
            description=data.get("description", ""),
            type=ToolType(tool_type),
            config=config,
            config_file=data.get("config_file"),
            readme=data.get("readme"),
            input_schema=data.get("input_schema", {}),
            output_schema=data.get("output_schema", {}),
            is_active=data.get("is_active", True),
            created_by=data.get("created_by"),
            execution_count={"total": 0, "success": 0, "failed": 0},
        )
        db.add(tool)
        await db.commit()
        await db.refresh(tool)
        logger.info(f"工具已创建: {tool.name} (类型: {tool.type})")
        return tool

    async def update_tool(self, db: AsyncSession, tool_id: UUID, data: dict) -> Optional[Tool]:
        """更新工具"""
        result = await db.execute(select(Tool).where(Tool.id == tool_id))
        tool = result.scalar_one_or_none()
        if not tool:
            return None

        # 如果更新了类型或配置，需要重新验证
        new_type = data.get("type", tool.type.value if isinstance(tool.type, ToolType) else tool.type)
        new_config = data.get("config", tool.config)

        adapter = AdapterRegistry.get(new_type)
        if not adapter:
            raise ValueError(f"不支持的工具类型: {new_type}")

        if "config" in data or "type" in data:
            is_valid, error = adapter.validate_config(new_config)
            if not is_valid:
                raise ValueError(f"配置验证失败: {error}")

        # 更新字段
        updatable = ["name", "description", "type", "config", "config_file", "readme", "input_schema", "output_schema", "is_active"]
        for field in updatable:
            if field in data:
                value = data[field]
                if field == "type":
                    value = ToolType(value)
                setattr(tool, field, value)

        tool.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(tool)
        logger.info(f"工具已更新: {tool.name}")
        return tool

    async def delete_tool(self, db: AsyncSession, tool_id: UUID) -> bool:
        """删除工具"""
        result = await db.execute(select(Tool).where(Tool.id == tool_id))
        tool = result.scalar_one_or_none()
        if not tool:
            return False

        await db.delete(tool)
        await db.commit()
        logger.info(f"工具已删除: {tool.name}")
        return True

    async def get_tool(self, db: AsyncSession, tool_id: UUID) -> Optional[Tool]:
        """获取单个工具"""
        result = await db.execute(select(Tool).where(Tool.id == tool_id))
        return result.scalar_one_or_none()

    async def get_tool_by_name(self, db: AsyncSession, name: str) -> Optional[Tool]:
        """按名称获取工具"""
        result = await db.execute(select(Tool).where(Tool.name == name))
        return result.scalar_one_or_none()

    async def list_tools(
        self, db: AsyncSession,
        tool_type: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[Tool]:
        """列出工具"""
        query = select(Tool)
        if tool_type:
            query = query.where(Tool.type == ToolType(tool_type))
        if is_active is not None:
            query = query.where(Tool.is_active == is_active)
        query = query.order_by(Tool.created_at.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    # ─── 执行 ────────────────────────────────────────────────

    async def execute_tool(
        self, db: AsyncSession,
        tool_id: UUID,
        params: dict,
        context: Optional[dict] = None,
    ) -> ToolResult:
        """
        执行工具。
        
        Args:
            db: 数据库会话
            tool_id: 工具ID
            params: 调用参数
            context: 执行上下文（conversation_id, agent_id 等）
        """
        tool = await self.get_tool(db, tool_id)
        if not tool:
            return ToolResult(success=False, error=f"工具不存在: {tool_id}")

        if not tool.is_active:
            return ToolResult(success=False, error=f"工具已禁用: {tool.name}")

        adapter = AdapterRegistry.get(tool.type.value if isinstance(tool.type, ToolType) else tool.type)
        if not adapter:
            return ToolResult(success=False, error=f"未找到适配器: {tool.type}")

        # 创建执行记录
        execution = ToolExecution(
            tool_id=tool.id,
            tool_name=tool.name,
            input_params=params,
            status="running",
            conversation_id=context.get("conversation_id") if context else None,
            agent_id=context.get("agent_id") if context else None,
        )
        db.add(execution)
        await db.commit()

        # 执行工具
        try:
            result = await adapter.execute(tool.config, tool.input_schema, params)

            # 更新执行记录
            execution.status = "success" if result.success else "failed"
            execution.output = result.to_dict()
            execution.error = result.error
            execution.completed_at = datetime.utcnow()
            execution.duration_ms = {"value": result.duration_ms}

            # 更新工具统计
            stats = tool.execution_count or {"total": 0, "success": 0, "failed": 0}
            stats["total"] = stats.get("total", 0) + 1
            if result.success:
                stats["success"] = stats.get("success", 0) + 1
            else:
                stats["failed"] = stats.get("failed", 0) + 1
            tool.execution_count = stats

            await db.commit()
            return result

        except Exception as e:
            execution.status = "failed"
            execution.error = str(e)
            execution.completed_at = datetime.utcnow()
            await db.commit()
            logger.error(f"工具执行异常: {tool.name} - {str(e)}")
            return ToolResult(success=False, error=f"执行异常: {str(e)}")

    async def execute_tool_by_name(
        self, db: AsyncSession,
        name: str,
        params: dict,
        context: Optional[dict] = None,
    ) -> ToolResult:
        """按名称执行工具"""
        tool = await self.get_tool_by_name(db, name)
        if not tool:
            return ToolResult(success=False, error=f"工具不存在: {name}")
        return await self.execute_tool(db, tool.id, params, context)

    # ─── 连通性测试 ──────────────────────────────────────────

    async def test_connection(self, db: AsyncSession, tool_id: UUID) -> ToolResult:
        """测试工具连通性"""
        tool = await self.get_tool(db, tool_id)
        if not tool:
            return ToolResult(success=False, error=f"工具不存在: {tool_id}")

        adapter = AdapterRegistry.get(tool.type.value if isinstance(tool.type, ToolType) else tool.type)
        if not adapter:
            return ToolResult(success=False, error=f"未找到适配器: {tool.type}")

        result = await adapter.test_connection(tool.config)

        # 更新健康状态
        tool.last_health_check = datetime.utcnow()
        tool.health_status = "healthy" if result.success else "unhealthy"
        tool.health_message = result.output if result.success else result.error
        await db.commit()

        return result

    async def test_config(self, tool_type: str, config: dict) -> ToolResult:
        """测试配置连通性（不需要先创建工具）"""
        adapter = AdapterRegistry.get(tool_type)
        if not adapter:
            return ToolResult(success=False, error=f"不支持的工具类型: {tool_type}")

        # 先验证配置
        is_valid, error = adapter.validate_config(config)
        if not is_valid:
            return ToolResult(success=False, error=f"配置验证失败: {error}")

        return await adapter.test_connection(config)

    # ─── Schema 生成 ─────────────────────────────────────────

    def tool_to_openai_schema(self, tool: Tool) -> dict:
        """将工具转换为 OpenAI function calling schema"""
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.input_schema or {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        }

    async def get_openai_schemas(
        self, db: AsyncSession,
        tool_names: Optional[List[str]] = None,
    ) -> List[dict]:
        """获取工具的 OpenAI function calling schemas"""
        query = select(Tool).where(Tool.is_active == True)
        if tool_names:
            query = query.where(Tool.name.in_(tool_names))
        result = await db.execute(query)
        tools = result.scalars().all()
        return [self.tool_to_openai_schema(t) for t in tools]

    # ─── 工具序列化 ──────────────────────────────────────────

    @staticmethod
    def tool_to_dict(tool: Tool) -> dict:
        """将工具模型转换为字典"""
        return {
            "id": str(tool.id),
            "name": tool.name,
            "description": tool.description,
            "type": tool.type.value if isinstance(tool.type, ToolType) else tool.type,
            "config": tool.config,
            "config_file": tool.config_file,
            "readme": tool.readme,
            "input_schema": tool.input_schema,
            "output_schema": tool.output_schema,
            "is_active": tool.is_active,
            "health_status": tool.health_status,
            "health_message": tool.health_message,
            "last_health_check": tool.last_health_check.isoformat() if tool.last_health_check else None,
            "execution_count": tool.execution_count,
            "created_at": tool.created_at.isoformat() if tool.created_at else None,
            "updated_at": tool.updated_at.isoformat() if tool.updated_at else None,
            "created_by": tool.created_by,
        }


# 全局单例
tool_manager = ToolManager()
