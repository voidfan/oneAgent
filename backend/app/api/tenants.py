"""Tenant API routes for multi-tenancy management."""
import uuid
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tenant import (
    Tenant, TenantStatus, TenantTool, TenantMCPConfig, TenantSkill, TenantContext
)
from app.middleware.tenant import get_current_tenant_id

router = APIRouter(prefix="/api/tenants", tags=["tenants"])


# ---- Pydantic Schemas ----

class TenantCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    description: Optional[str] = None
    settings: dict = {}
    max_users: int = 10
    max_agents: int = 50


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TenantStatus] = None
    settings: Optional[dict] = None
    max_users: Optional[int] = None
    max_agents: Optional[int] = None
    max_conversations_per_day: Optional[int] = None
    max_tokens_per_month: Optional[int] = None


class TenantOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: Optional[str]
    status: TenantStatus
    settings: dict
    max_users: int
    max_agents: int
    max_conversations_per_day: int
    max_tokens_per_month: int
    current_month_tokens: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TenantToolCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    tool_type: str = "custom"
    parameters_schema: dict = {}
    implementation: Optional[str] = None
    is_enabled: bool = True
    requires_approval: bool = False
    config: dict = {}


class TenantToolOut(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    description: Optional[str]
    tool_type: str
    parameters_schema: dict
    is_enabled: bool
    requires_approval: bool
    config: dict
    created_at: datetime

    class Config:
        from_attributes = True


class TenantMCPCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    server_url: str
    transport_type: str = "stdio"
    auth_type: Optional[str] = None
    auth_config: dict = {}
    is_enabled: bool = True
    config: dict = {}


class TenantMCPOut(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    description: Optional[str]
    server_url: str
    transport_type: str
    auth_type: Optional[str]
    available_tools: dict
    is_enabled: bool
    config: dict
    created_at: datetime

    class Config:
        from_attributes = True


class TenantSkillCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    system_prompt: Optional[str] = None
    user_prompt_template: Optional[str] = None
    required_tools: list = []
    parameters: dict = {}
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    is_enabled: bool = True
    is_public: bool = False


class TenantSkillOut(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    description: Optional[str]
    category: Optional[str]
    system_prompt: Optional[str]
    user_prompt_template: Optional[str]
    required_tools: list
    parameters: dict
    llm_provider: Optional[str]
    llm_model: Optional[str]
    temperature: float
    is_enabled: bool
    is_public: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TenantContextCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    context_type: str = "document"
    content: Optional[str] = None
    source_url: Optional[str] = None
    metadata_: dict = Field(default={}, alias="metadata")
    is_enabled: bool = True


class TenantContextOut(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    description: Optional[str]
    context_type: str
    content: Optional[str]
    source_url: Optional[str]
    embedding_collection: Optional[str]
    chunk_count: int
    is_enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TenantSettingsUpdate(BaseModel):
    """Update tenant-level settings (LLM, etc.)"""
    llm: Optional[dict] = None
    agent_defaults: Optional[dict] = None
    memory: Optional[dict] = None
    observability: Optional[dict] = None
    security: Optional[dict] = None


# ---- Tenant CRUD ----

@router.get("", response_model=list[TenantOut])
async def list_tenants(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List all tenants (admin only)."""
    result = await db.execute(
        select(Tenant)
        .order_by(Tenant.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()


@router.post("", response_model=TenantOut)
async def create_tenant(data: TenantCreate, db: AsyncSession = Depends(get_db)):
    """Create a new tenant."""
    # Check slug uniqueness
    existing = await db.execute(
        select(Tenant).where(Tenant.slug == data.slug)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Tenant slug already exists")
    
    tenant = Tenant(
        name=data.name,
        slug=data.slug,
        description=data.description,
        settings=data.settings,
        max_users=data.max_users,
        max_agents=data.max_agents,
    )
    db.add(tenant)
    await db.flush()
    await db.refresh(tenant)
    return tenant


@router.get("/{tenant_id}", response_model=TenantOut)
async def get_tenant(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get tenant by ID."""
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


@router.put("/{tenant_id}", response_model=TenantOut)
async def update_tenant(
    tenant_id: uuid.UUID,
    data: TenantUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update tenant."""
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(tenant, key, value)
    
    await db.flush()
    await db.refresh(tenant)
    return tenant


@router.delete("/{tenant_id}")
async def delete_tenant(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Delete tenant (soft delete by setting status to suspended)."""
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    tenant.status = TenantStatus.SUSPENDED
    await db.flush()
    return {"status": "deleted", "tenant_id": str(tenant_id)}


# ---- Tenant Settings ----

@router.get("/{tenant_id}/settings", response_model=dict)
async def get_tenant_settings(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get tenant settings."""
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant.settings or {}


@router.put("/{tenant_id}/settings", response_model=dict)
async def update_tenant_settings(
    tenant_id: uuid.UUID,
    data: TenantSettingsUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update tenant settings."""
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    settings = tenant.settings or {}
    update_data = data.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        if value is not None:
            settings[key] = value
    
    tenant.settings = settings
    await db.flush()
    return tenant.settings


# ---- Tenant Tools ----

@router.get("/{tenant_id}/tools", response_model=list[TenantToolOut])
async def list_tenant_tools(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """List tools for a tenant."""
    result = await db.execute(
        select(TenantTool)
        .where(TenantTool.tenant_id == tenant_id)
        .order_by(TenantTool.name)
    )
    return result.scalars().all()


@router.post("/{tenant_id}/tools", response_model=TenantToolOut)
async def create_tenant_tool(
    tenant_id: uuid.UUID,
    data: TenantToolCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a tool for a tenant."""
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    tool = TenantTool(
        tenant_id=tenant_id,
        name=data.name,
        description=data.description,
        tool_type=data.tool_type,
        parameters_schema=data.parameters_schema,
        implementation=data.implementation,
        is_enabled=data.is_enabled,
        requires_approval=data.requires_approval,
        config=data.config,
    )
    db.add(tool)
    await db.flush()
    await db.refresh(tool)
    return tool


@router.delete("/{tenant_id}/tools/{tool_id}")
async def delete_tenant_tool(
    tenant_id: uuid.UUID,
    tool_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a tenant tool."""
    result = await db.execute(
        select(TenantTool).where(
            TenantTool.id == tool_id,
            TenantTool.tenant_id == tenant_id
        )
    )
    tool = result.scalar_one_or_none()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    await db.delete(tool)
    return {"status": "deleted"}


# ---- Tenant MCP Configs ----

@router.get("/{tenant_id}/mcp", response_model=list[TenantMCPOut])
async def list_tenant_mcp_configs(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """List MCP configurations for a tenant."""
    result = await db.execute(
        select(TenantMCPConfig)
        .where(TenantMCPConfig.tenant_id == tenant_id)
        .order_by(TenantMCPConfig.name)
    )
    return result.scalars().all()


@router.post("/{tenant_id}/mcp", response_model=TenantMCPOut)
async def create_tenant_mcp_config(
    tenant_id: uuid.UUID,
    data: TenantMCPCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create an MCP configuration for a tenant."""
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    mcp = TenantMCPConfig(
        tenant_id=tenant_id,
        name=data.name,
        description=data.description,
        server_url=data.server_url,
        transport_type=data.transport_type,
        auth_type=data.auth_type,
        auth_config=data.auth_config,
        is_enabled=data.is_enabled,
        config=data.config,
    )
    db.add(mcp)
    await db.flush()
    await db.refresh(mcp)
    return mcp


@router.delete("/{tenant_id}/mcp/{mcp_id}")
async def delete_tenant_mcp_config(
    tenant_id: uuid.UUID,
    mcp_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a tenant MCP configuration."""
    result = await db.execute(
        select(TenantMCPConfig).where(
            TenantMCPConfig.id == mcp_id,
            TenantMCPConfig.tenant_id == tenant_id
        )
    )
    mcp = result.scalar_one_or_none()
    if not mcp:
        raise HTTPException(status_code=404, detail="MCP config not found")
    
    await db.delete(mcp)
    return {"status": "deleted"}


# ---- Tenant Skills ----

@router.get("/{tenant_id}/skills", response_model=list[TenantSkillOut])
async def list_tenant_skills(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """List skills for a tenant."""
    result = await db.execute(
        select(TenantSkill)
        .where(TenantSkill.tenant_id == tenant_id)
        .order_by(TenantSkill.name)
    )
    return result.scalars().all()


@router.post("/{tenant_id}/skills", response_model=TenantSkillOut)
async def create_tenant_skill(
    tenant_id: uuid.UUID,
    data: TenantSkillCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a skill for a tenant."""
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    skill = TenantSkill(
        tenant_id=tenant_id,
        name=data.name,
        description=data.description,
        category=data.category,
        system_prompt=data.system_prompt,
        user_prompt_template=data.user_prompt_template,
        required_tools=data.required_tools,
        parameters=data.parameters,
        llm_provider=data.llm_provider,
        llm_model=data.llm_model,
        temperature=data.temperature,
        max_tokens=data.max_tokens,
        is_enabled=data.is_enabled,
        is_public=data.is_public,
    )
    db.add(skill)
    await db.flush()
    await db.refresh(skill)
    return skill


@router.delete("/{tenant_id}/skills/{skill_id}")
async def delete_tenant_skill(
    tenant_id: uuid.UUID,
    skill_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a tenant skill."""
    result = await db.execute(
        select(TenantSkill).where(
            TenantSkill.id == skill_id,
            TenantSkill.tenant_id == tenant_id
        )
    )
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    await db.delete(skill)
    return {"status": "deleted"}


# ---- Tenant Contexts ----

@router.get("/{tenant_id}/contexts", response_model=list[TenantContextOut])
async def list_tenant_contexts(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """List context/knowledge base entries for a tenant."""
    result = await db.execute(
        select(TenantContext)
        .where(TenantContext.tenant_id == tenant_id)
        .order_by(TenantContext.name)
    )
    return result.scalars().all()


@router.post("/{tenant_id}/contexts", response_model=TenantContextOut)
async def create_tenant_context(
    tenant_id: uuid.UUID,
    data: TenantContextCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a context entry for a tenant."""
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    context = TenantContext(
        tenant_id=tenant_id,
        name=data.name,
        description=data.description,
        context_type=data.context_type,
        content=data.content,
        source_url=data.source_url,
        metadata_=data.metadata_,
        is_enabled=data.is_enabled,
    )
    db.add(context)
    await db.flush()
    await db.refresh(context)
    return context


@router.delete("/{tenant_id}/contexts/{context_id}")
async def delete_tenant_context(
    tenant_id: uuid.UUID,
    context_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a tenant context entry."""
    result = await db.execute(
        select(TenantContext).where(
            TenantContext.id == context_id,
            TenantContext.tenant_id == tenant_id
        )
    )
    context = result.scalar_one_or_none()
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")
    
    await db.delete(context)
    return {"status": "deleted"}


# ---- Current Tenant Shortcut ----

@router.get("/current/info", response_model=TenantOut)
async def get_current_tenant_info(db: AsyncSession = Depends(get_db)):
    """Get current tenant info based on context."""
    tenant_id = get_current_tenant_id()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context")
    
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant
