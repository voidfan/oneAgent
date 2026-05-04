"""FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.observability.logger import setup_logging
from app.tools.adapters import register_adapters
from app.middleware.tenant import TenantMiddleware
from app.api.chat import router as chat_router
from app.api.agents import router as agents_router
from app.api.tools import router as tools_router
from app.api.system import router as system_router
from app.api.settings import router as settings_router
from app.api.tenants import router as tenants_router
from app.api.workflows import router as workflows_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    setup_logging()
    await init_db()
    register_adapters()
    yield
    # Shutdown


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI Agent Framework with multi-tenancy, multi-agent collaboration, tool use, and memory systems.",
    lifespan=lifespan,
)

# Tenant isolation middleware (must be added before CORS)
app.add_middleware(TenantMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(chat_router)
app.include_router(agents_router)
app.include_router(tools_router)
app.include_router(system_router)
app.include_router(settings_router)
app.include_router(tenants_router)
app.include_router(workflows_router)


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "multi_tenant": True,
    }
