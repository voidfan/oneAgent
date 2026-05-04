from sqlalchemy import Column, String, Text, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from ..database import Base


class Workflow(Base):
    """工作流模型 - 存储 Puck 设计器生成的工作流配置"""
    __tablename__ = "workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    slug = Column(String(100), nullable=False, unique=True)

    # Puck 编辑器保存的 JSON 数据（包含组件树、布局等）
    puck_data = Column(JSON, nullable=True, default=dict)

    # 工作流绑定的 Agent ID（可选）
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)

    # 工作流配置：系统提示词、欢迎语等
    config = Column(JSON, nullable=True, default=dict)

    # 是否公开（可通过分享链接访问）
    is_public = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # 租户隔离
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关联（单向，不在 Agent/Tenant 上定义 back_populates）
    agent = relationship("Agent", foreign_keys=[agent_id])
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    sessions = relationship("WorkflowSession", back_populates="workflow", cascade="all, delete-orphan")


class WorkflowSession(Base):
    """工作流会话 - 每次运行工作流时创建的对话会话"""
    __tablename__ = "workflow_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)

    # 会话状态
    status = Column(String(50), default="active")  # active, completed, error

    # 会话消息历史（JSON 数组）
    messages = Column(JSON, nullable=True, default=list)

    # 会话元数据
    session_metadata = Column(JSON, nullable=True, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关联
    workflow = relationship("Workflow", back_populates="sessions")
