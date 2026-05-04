"""System API routes - health, metrics, traces."""
import time

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest

from app.config import settings
from app.api.schemas import HealthResponse, SystemStats
from app.observability.metrics import metrics_registry
from app.observability.tracing import TraceCollector

router = APIRouter(prefix="/api/system", tags=["system"])

_start_time = time.time()
trace_collector = TraceCollector()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        version=settings.APP_VERSION,
        uptime_seconds=round(time.time() - _start_time, 2),
    )


@router.get("/stats", response_model=SystemStats)
async def system_stats():
    """Get system statistics."""
    return SystemStats(
        llm_provider=settings.DEFAULT_LLM_PROVIDER,
    )


@router.get("/traces")
async def list_traces(limit: int = 50):
    """List recent execution traces."""
    return trace_collector.get_recent_traces(limit)


@router.get("/traces/{trace_id}")
async def get_trace(trace_id: str):
    """Get detailed trace information."""
    spans = trace_collector.get_trace(trace_id)
    if not spans:
        return {"error": "Trace not found"}
    return {"trace_id": trace_id, "spans": spans}


@router.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics():
    """Prometheus metrics endpoint."""
    return generate_latest(metrics_registry).decode("utf-8")
