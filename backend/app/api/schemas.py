"""Pydantic schemas for API request/response validation."""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ---- Chat / Conversation ----

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=50000)
    conversation_id: Optional[UUID] = None
    agent_id: Optional[UUID] = None
    stream: bool = False


class ChatResponse(BaseModel):
    conversation_id: UUID
    message_id: UUID
    content: str
    role: str = "assistant"
    tokens_used: int = 0
    tool_calls: list[dict] = []


class MessageOut(BaseModel):
    id: UUID
    role: str
    content: str
    token_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationOut(BaseModel):
    id: UUID
    title: Optional[str] = None
    agent_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    messages: list[MessageOut] = []

    class Config:
        from_attributes = True


# ---- Agent ----

class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    llm_provider: str = "openai"
    llm_model: Optional[str] = None
    max_steps: int = Field(default=50, ge=1, le=200)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    tools_config: dict = {}


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    max_steps: Optional[int] = None
    temperature: Optional[float] = None
    tools_config: Optional[dict] = None


class AgentOut(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    llm_provider: str
    llm_model: Optional[str] = None
    max_steps: int
    temperature: float
    tools_config: dict = {}
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ---- Tool ----

class ToolCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    type: str  # mcp / api / agent / script / sandbox
    config: dict = {}
    config_file: Optional[str] = None   # 配置文件内容（YAML/JSON）
    readme: Optional[str] = None        # 说明文件内容（Markdown）
    input_schema: dict = {}
    output_schema: dict = {}
    is_active: bool = True


class ToolUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    config: Optional[dict] = None
    config_file: Optional[str] = None
    readme: Optional[str] = None
    input_schema: Optional[dict] = None
    output_schema: Optional[dict] = None
    is_active: Optional[bool] = None


class ToolOut(BaseModel):
    id: str
    name: str
    description: Optional[str] = ""
    type: str
    config: dict = {}
    config_file: Optional[str] = None
    readme: Optional[str] = None
    input_schema: dict = {}
    output_schema: dict = {}
    is_active: bool = True
    health_status: Optional[str] = "unknown"
    health_message: Optional[str] = None
    last_health_check: Optional[str] = None
    execution_count: dict = {}
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ToolExecuteRequest(BaseModel):
    tool_name: Optional[str] = None
    tool_id: Optional[str] = None
    params: dict = {}
    context: Optional[dict] = None


class ToolExecuteResponse(BaseModel):
    success: bool
    output: Any = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None
    metadata: dict = {}


class ToolTestRequest(BaseModel):
    type: str
    config: dict = {}


class ToolTestResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    duration_ms: Optional[float] = None


# ---- Execution / Trace ----

class ExecutionOut(BaseModel):
    id: UUID
    agent_id: UUID
    status: str
    goal: Optional[str] = None
    result: Optional[str] = None
    total_tokens: int = 0
    total_cost: float = 0.0
    step_count: int = 0
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StepOut(BaseModel):
    id: UUID
    step_number: int
    step_type: str
    input_data: dict = {}
    output_data: dict = {}
    reasoning: Optional[str] = None
    tokens_used: int = 0
    duration_ms: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


# ---- System ----

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    uptime_seconds: float


class SystemStats(BaseModel):
    active_agents: int = 0
    total_conversations: int = 0
    total_tokens_used: int = 0
    total_tool_executions: int = 0
    llm_provider: str = ""
