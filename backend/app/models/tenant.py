"""Tenant model for multi-tenancy support."""
import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TenantStatus(str, PyEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"


class Tenant(Base):
    """Tenant represents an isolated workspace with its own configuration."""
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), index=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default=TenantStatus.ACTIVE
    )
    
    # Tenant-level settings stored as JSON
    settings: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Quota and limits
    max_users: Mapped[int] = mapped_column(default=10)
    max_agents: Mapped[int] = mapped_column(default=50)
    max_conversations_per_day: Mapped[int] = mapped_column(default=1000)
    max_tokens_per_month: Mapped[int] = mapped_column(default=10000000)
    
    # Usage tracking
    current_month_tokens: Mapped[int] = mapped_column(default=0)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    users = relationship("User", back_populates="tenant", lazy="selectin")
    agents = relationship("Agent", back_populates="tenant", lazy="selectin")
    tools = relationship("TenantTool", back_populates="tenant", lazy="selectin")
    mcp_configs = relationship("TenantMCPConfig", back_populates="tenant", lazy="selectin")
    skills = relationship("TenantSkill", back_populates="tenant", lazy="selectin")


class TenantTool(Base):
    """Tenant-specific tool configuration."""
    __tablename__ = "tenant_tools"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE")
    )
    tool_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tools.id"), nullable=True
    )
    
    # Custom tool definition (if not referencing global tool)
    name: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    tool_type: Mapped[str] = mapped_column(String(50), default="custom")
    parameters_schema: Mapped[dict] = mapped_column(JSON, default=dict)
    implementation: Mapped[str] = mapped_column(Text, nullable=True)  # Code or module path
    
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    tenant = relationship("Tenant", back_populates="tools")


class TenantMCPConfig(Base):
    """Tenant-specific MCP server configuration."""
    __tablename__ = "tenant_mcp_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE")
    )
    
    name: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    server_url: Mapped[str] = mapped_column(String(500))
    transport_type: Mapped[str] = mapped_column(String(50), default="stdio")  # stdio, http, websocket
    
    # Authentication
    auth_type: Mapped[str] = mapped_column(String(50), nullable=True)  # none, api_key, oauth
    auth_config: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Available tools from this MCP server
    available_tools: Mapped[dict] = mapped_column(JSON, default=dict)
    
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    tenant = relationship("Tenant", back_populates="mcp_configs")


class TenantSkill(Base):
    """Tenant-specific skill/prompt template."""
    __tablename__ = "tenant_skills"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE")
    )
    
    name: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=True)
    
    # Skill definition
    system_prompt: Mapped[str] = mapped_column(Text, nullable=True)
    user_prompt_template: Mapped[str] = mapped_column(Text, nullable=True)
    required_tools: Mapped[list] = mapped_column(JSON, default=list)
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Execution settings
    llm_provider: Mapped[str] = mapped_column(String(50), nullable=True)
    llm_model: Mapped[str] = mapped_column(String(100), nullable=True)
    temperature: Mapped[float] = mapped_column(default=0.7)
    max_tokens: Mapped[int] = mapped_column(nullable=True)
    
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)  # Share with other tenants
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    tenant = relationship("Tenant", back_populates="skills")


class TenantContext(Base):
    """Tenant-specific context/knowledge base entries."""
    __tablename__ = "tenant_contexts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    
    name: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    context_type: Mapped[str] = mapped_column(String(50), default="document")  # document, url, api
    
    # Content
    content: Mapped[str] = mapped_column(Text, nullable=True)
    source_url: Mapped[str] = mapped_column(String(1000), nullable=True)
    
    # Vector embedding reference
    embedding_collection: Mapped[str] = mapped_column(String(200), nullable=True)
    chunk_count: Mapped[int] = mapped_column(default=0)
    
    # Metadata
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
