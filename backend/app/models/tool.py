"""Tool models."""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional
from sqlalchemy import Column, String, Text, Boolean, DateTime, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.database import Base


class ToolType(str, PyEnum):
    """工具类型枚举"""
    MCP = "mcp"           # MCP协议工具
    API = "api"           # HTTP API服务工具
    AGENT = "agent"       # 子Agent工具
    SCRIPT = "script"     # 本地可执行脚本
    SANDBOX = "sandbox"   # 沙箱运行代码
    SKILLS = "skills"     # 技能工具（可复用的预定义能力）


class Tool(Base):
    """工具模型 - 支持多种工具类型的统一模型"""
    __tablename__ = "tools"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    type = Column(Enum(ToolType), nullable=False, index=True)
    
    # 工具配置（JSON格式，根据类型存储不同配置）
    # MCP: {"server_url": "...", "auth": {...}}
    # API: {"endpoint": "...", "method": "POST", "headers": {...}, "auth": {...}}
    # Agent: {"agent_id": "..."}
    # Script: {"script_path": "...", "interpreter": "python"}
    # Sandbox: {"code": "...", "allowed_modules": [...]}
    config = Column(JSON, nullable=False, default=dict)
    
    # 配置文件内容（YAML/JSON格式的完整配置文件，可直接用于运行工具）
    config_file = Column(Text, nullable=True)
    # 说明文件内容（Markdown格式的工具使用说明）
    readme = Column(Text, nullable=True)
    
    # 工具输入输出 schema（OpenAI function calling 格式）
    input_schema = Column(JSON, nullable=False, default=dict)
    output_schema = Column(JSON, default=dict)
    
    # 状态管理
    is_active = Column(Boolean, default=True, index=True)
    last_health_check = Column(DateTime, nullable=True)
    health_status = Column(String(50), default="unknown")  # unknown, healthy, unhealthy
    health_message = Column(Text, nullable=True)
    
    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=True)
    
    # 统计信息
    execution_count = Column(JSON, default=dict)  # {"total": 0, "success": 0, "failed": 0}
    
    def __repr__(self):
        return f"<Tool(name={self.name}, type={self.type}, active={self.is_active})>"


class ToolExecution(Base):
    """工具执行记录"""
    __tablename__ = "tool_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tool_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    tool_name = Column(String(100), nullable=False)
    
    # 执行参数和结果
    input_params = Column(JSON, nullable=False)
    output = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    
    # 执行状态
    status = Column(String(20), nullable=False)  # pending, running, success, failed
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(JSON, nullable=True)  # 执行耗时（毫秒）
    
    # 执行上下文
    conversation_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    agent_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    def __repr__(self):
        return f"<ToolExecution(tool={self.tool_name}, status={self.status})>"
