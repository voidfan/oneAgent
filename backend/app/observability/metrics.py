"""Prometheus metrics for monitoring."""
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry

# Custom registry to avoid conflicts
metrics_registry = CollectorRegistry()

# Request metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
    registry=metrics_registry,
)

http_request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint"],
    registry=metrics_registry,
)

# Agent metrics
agent_executions_total = Counter(
    "agent_executions_total",
    "Total agent executions",
    ["agent_id", "status"],
    registry=metrics_registry,
)

agent_steps_total = Counter(
    "agent_steps_total",
    "Total agent steps",
    ["agent_id", "step_type"],
    registry=metrics_registry,
)

agent_active = Gauge(
    "agent_active_count",
    "Number of currently active agents",
    registry=metrics_registry,
)

# LLM metrics
llm_requests_total = Counter(
    "llm_requests_total",
    "Total LLM API requests",
    ["provider", "model"],
    registry=metrics_registry,
)

llm_tokens_total = Counter(
    "llm_tokens_total",
    "Total tokens used",
    ["provider", "model", "type"],  # type: prompt | completion
    registry=metrics_registry,
)

llm_request_duration = Histogram(
    "llm_request_duration_seconds",
    "LLM request duration",
    ["provider", "model"],
    registry=metrics_registry,
)

# Tool metrics
tool_executions_total = Counter(
    "tool_executions_total",
    "Total tool executions",
    ["tool_name", "status"],
    registry=metrics_registry,
)

tool_execution_duration = Histogram(
    "tool_execution_duration_seconds",
    "Tool execution duration",
    ["tool_name"],
    registry=metrics_registry,
)

# Memory metrics
memory_operations_total = Counter(
    "memory_operations_total",
    "Total memory operations",
    ["memory_type", "operation"],  # operation: read | write | delete
    registry=metrics_registry,
)
