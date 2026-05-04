"""Tenant middleware and context management for multi-tenancy."""
import uuid
import logging
from contextvars import ContextVar
from typing import Optional

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory

logger = logging.getLogger(__name__)

# Context variable to store current tenant ID
_current_tenant_id: ContextVar[Optional[uuid.UUID]] = ContextVar("current_tenant_id", default=None)
_current_user_id: ContextVar[Optional[uuid.UUID]] = ContextVar("current_user_id", default=None)


def get_current_tenant_id() -> Optional[uuid.UUID]:
    """Get the current tenant ID from context."""
    return _current_tenant_id.get()


def set_current_tenant_id(tenant_id: Optional[uuid.UUID]) -> None:
    """Set the current tenant ID in context."""
    _current_tenant_id.set(tenant_id)


def get_current_user_id() -> Optional[uuid.UUID]:
    """Get the current user ID from context."""
    return _current_user_id.get()


def set_current_user_id(user_id: Optional[uuid.UUID]) -> None:
    """Set the current user ID in context."""
    _current_user_id.set(user_id)


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware to extract and validate tenant from request."""
    
    # Paths that don't require tenant context
    PUBLIC_PATHS = {
        "/",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/system/health",
        "/api/system/stats",
        "/api/auth/login",
        "/api/auth/register",
        "/api/tenants",  # Tenant management (admin only)
    }
    
    async def dispatch(self, request: Request, call_next):
        # Skip tenant check for public paths
        path = request.url.path
        if path in self.PUBLIC_PATHS or path.startswith("/api/system/"):
            return await call_next(request)
        
        # Extract tenant from various sources
        tenant_id = await self._extract_tenant_id(request)
        
        if tenant_id:
            # Validate tenant exists and is active
            is_valid = await self._validate_tenant(tenant_id)
            if not is_valid:
                raise HTTPException(status_code=403, detail="Invalid or inactive tenant")
            
            # Set tenant in context
            set_current_tenant_id(tenant_id)
            logger.debug(f"Tenant context set: {tenant_id}")
        
        # Extract user ID from request (if authenticated)
        user_id = await self._extract_user_id(request)
        if user_id:
            set_current_user_id(user_id)
        
        try:
            response = await call_next(request)
            return response
        finally:
            # Clear context after request
            set_current_tenant_id(None)
            set_current_user_id(None)
    
    async def _extract_tenant_id(self, request: Request) -> Optional[uuid.UUID]:
        """Extract tenant ID from request headers, query params, or path."""
        # 1. Check X-Tenant-ID header
        tenant_header = request.headers.get("X-Tenant-ID")
        if tenant_header:
            try:
                return uuid.UUID(tenant_header)
            except ValueError:
                pass
        
        # 2. Check query parameter
        tenant_param = request.query_params.get("tenant_id")
        if tenant_param:
            try:
                return uuid.UUID(tenant_param)
            except ValueError:
                pass
        
        # 3. Check path parameter (for /api/tenants/{tenant_id}/... routes)
        path_parts = request.url.path.split("/")
        if len(path_parts) >= 4 and path_parts[2] == "tenants":
            try:
                return uuid.UUID(path_parts[3])
            except ValueError:
                pass
        
        # 4. Default tenant (for single-tenant mode or development)
        # In production, you might want to require tenant ID
        return None
    
    async def _extract_user_id(self, request: Request) -> Optional[uuid.UUID]:
        """Extract user ID from request (from JWT token or session)."""
        # Check X-User-ID header (set by auth middleware)
        user_header = request.headers.get("X-User-ID")
        if user_header:
            try:
                return uuid.UUID(user_header)
            except ValueError:
                pass
        return None
    
    async def _validate_tenant(self, tenant_id: uuid.UUID) -> bool:
        """Validate that tenant exists and is active."""
        from app.models.tenant import Tenant, TenantStatus
        
        async with async_session_factory() as session:
            result = await session.execute(
                select(Tenant).where(
                    Tenant.id == tenant_id,
                    Tenant.status == TenantStatus.ACTIVE
                )
            )
            tenant = result.scalar_one_or_none()
            return tenant is not None


class TenantQueryMixin:
    """Mixin to add tenant filtering to database queries."""
    
    @staticmethod
    def filter_by_tenant(query, model_class, tenant_id: Optional[uuid.UUID] = None):
        """Add tenant filter to a query if tenant context is set."""
        tid = tenant_id or get_current_tenant_id()
        if tid and hasattr(model_class, 'tenant_id'):
            return query.where(model_class.tenant_id == tid)
        return query
    
    @staticmethod
    def set_tenant_on_create(instance, tenant_id: Optional[uuid.UUID] = None):
        """Set tenant_id on a new model instance."""
        tid = tenant_id or get_current_tenant_id()
        if tid and hasattr(instance, 'tenant_id'):
            instance.tenant_id = tid
        return instance


async def get_tenant_settings(tenant_id: Optional[uuid.UUID] = None) -> dict:
    """Get settings for the current or specified tenant."""
    from app.models.tenant import Tenant
    
    tid = tenant_id or get_current_tenant_id()
    if not tid:
        # Return default settings if no tenant context
        return {}
    
    async with async_session_factory() as session:
        result = await session.execute(
            select(Tenant).where(Tenant.id == tid)
        )
        tenant = result.scalar_one_or_none()
        if tenant:
            return tenant.settings or {}
    return {}


async def get_tenant_llm_config(tenant_id: Optional[uuid.UUID] = None) -> dict:
    """Get LLM configuration for the current or specified tenant."""
    settings = await get_tenant_settings(tenant_id)
    return settings.get("llm", {})


async def get_tenant_tools(tenant_id: Optional[uuid.UUID] = None) -> list:
    """Get enabled tools for the current or specified tenant."""
    from app.models.tenant import TenantTool
    
    tid = tenant_id or get_current_tenant_id()
    if not tid:
        return []
    
    async with async_session_factory() as session:
        result = await session.execute(
            select(TenantTool).where(
                TenantTool.tenant_id == tid,
                TenantTool.is_enabled == True
            )
        )
        return result.scalars().all()


async def get_tenant_mcp_configs(tenant_id: Optional[uuid.UUID] = None) -> list:
    """Get MCP configurations for the current or specified tenant."""
    from app.models.tenant import TenantMCPConfig
    
    tid = tenant_id or get_current_tenant_id()
    if not tid:
        return []
    
    async with async_session_factory() as session:
        result = await session.execute(
            select(TenantMCPConfig).where(
                TenantMCPConfig.tenant_id == tid,
                TenantMCPConfig.is_enabled == True
            )
        )
        return result.scalars().all()


async def get_tenant_skills(tenant_id: Optional[uuid.UUID] = None) -> list:
    """Get skills for the current or specified tenant."""
    from app.models.tenant import TenantSkill
    
    tid = tenant_id or get_current_tenant_id()
    if not tid:
        return []
    
    async with async_session_factory() as session:
        result = await session.execute(
            select(TenantSkill).where(
                TenantSkill.tenant_id == tid,
                TenantSkill.is_enabled == True
            )
        )
        return result.scalars().all()


async def get_tenant_contexts(tenant_id: Optional[uuid.UUID] = None) -> list:
    """Get context/knowledge base entries for the current or specified tenant."""
    from app.models.tenant import TenantContext
    
    tid = tenant_id or get_current_tenant_id()
    if not tid:
        return []
    
    async with async_session_factory() as session:
        result = await session.execute(
            select(TenantContext).where(
                TenantContext.tenant_id == tid,
                TenantContext.is_enabled == True
            )
        )
        return result.scalars().all()
