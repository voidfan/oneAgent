"""Workflow API - CRUD for Puck-based workflow designer."""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.database import get_db
from app.models.workflow import Workflow, WorkflowSession
from app.llm.factory import get_llm_provider

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


def _parse_uuid(value: Optional[str]) -> Optional[uuid.UUID]:
    """Safely parse a string to UUID, return None if invalid or None."""
    if not value:
        return None
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail=f"Invalid UUID: {value}")


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    slug: Optional[str] = None
    puck_data: Optional[dict] = None
    agent_id: Optional[str] = None
    config: Optional[dict] = None
    is_public: bool = False


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    slug: Optional[str] = None
    puck_data: Optional[dict] = None
    agent_id: Optional[str] = None
    config: Optional[dict] = None
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None


class WorkflowPublishRequest(BaseModel):
    """发布/取消发布请求"""
    is_public: bool = True


class WorkflowResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    slug: str
    puck_data: Optional[dict]
    agent_id: Optional[str]
    config: Optional[dict]
    is_public: bool
    is_active: bool
    created_at: Optional[str]
    updated_at: Optional[str]

    class Config:
        from_attributes = True


class ChatMessage(BaseModel):
    role: str  # user / assistant
    content: str


class WorkflowChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    history: Optional[List[ChatMessage]] = None


class WorkflowChatResponse(BaseModel):
    session_id: str
    message: str
    role: str = "assistant"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _wf_to_dict(wf: Workflow) -> dict:
    return {
        "id": str(wf.id),
        "name": wf.name,
        "description": wf.description,
        "slug": wf.slug,
        "puck_data": wf.puck_data or {},
        "agent_id": str(wf.agent_id) if wf.agent_id else None,
        "config": wf.config or {},
        "is_public": wf.is_public,
        "is_active": wf.is_active,
        "created_at": wf.created_at.isoformat() if wf.created_at else None,
        "updated_at": wf.updated_at.isoformat() if wf.updated_at else None,
    }


def _make_slug(name: str) -> str:
    import re
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    slug = slug.strip("-")
    return slug or str(uuid.uuid4())[:8]


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("", response_model=List[dict])
async def list_workflows(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workflow).where(Workflow.is_active == True).order_by(Workflow.created_at.desc()))
    workflows = result.scalars().all()
    return [_wf_to_dict(w) for w in workflows]


@router.post("", response_model=dict)
async def create_workflow(data: WorkflowCreate, db: AsyncSession = Depends(get_db)):
    slug = data.slug or _make_slug(data.name)
    # Ensure slug uniqueness
    existing = await db.execute(select(Workflow).where(Workflow.slug == slug))
    if existing.scalar_one_or_none():
        slug = f"{slug}-{str(uuid.uuid4())[:6]}"

    wf = Workflow(
        name=data.name,
        description=data.description,
        slug=slug,
        puck_data=data.puck_data or {},
        agent_id=_parse_uuid(data.agent_id),
        config=data.config or {},
        is_public=data.is_public,
    )
    db.add(wf)
    await db.flush()
    await db.refresh(wf)
    return _wf_to_dict(wf)


@router.get("/{workflow_id}", response_model=dict)
async def get_workflow(workflow_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workflow).where(Workflow.id == _parse_uuid(workflow_id)))
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return _wf_to_dict(wf)


@router.get("/by-slug/{slug}", response_model=dict)
async def get_workflow_by_slug(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workflow).where(Workflow.slug == slug))
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return _wf_to_dict(wf)


@router.get("/public/{slug}", response_model=dict)
async def get_public_workflow(slug: str, db: AsyncSession = Depends(get_db)):
    """公开访问已发布的工作流应用（无需认证）"""
    result = await db.execute(
        select(Workflow).where(Workflow.slug == slug, Workflow.is_public == True, Workflow.is_active == True)
    )
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="应用未找到或未发布")
    return _wf_to_dict(wf)


@router.post("/public/{slug}/chat", response_model=WorkflowChatResponse)
async def public_workflow_chat(
    slug: str,
    req: WorkflowChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """公开应用的聊天端点（无需认证）"""
    result = await db.execute(
        select(Workflow).where(Workflow.slug == slug, Workflow.is_public == True, Workflow.is_active == True)
    )
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="应用未找到或未发布")

    # Get or create session
    session_id = req.session_id or str(uuid.uuid4())
    session_uuid = uuid.UUID(session_id)
    session = None
    if req.session_id:
        sess_result = await db.execute(
            select(WorkflowSession).where(WorkflowSession.id == session_uuid)
        )
        session = sess_result.scalar_one_or_none()

    if not session:
        session = WorkflowSession(
            id=session_uuid,
            workflow_id=wf.id,
            messages=[],
        )
        db.add(session)

    # Build message history
    history = session.messages or []
    history.append({"role": "user", "content": req.message})

    # Build system prompt from workflow config
    config = wf.config or {}
    system_prompt = config.get("system_prompt", "You are a helpful AI assistant.")

    # Call LLM
    try:
        llm = get_llm_provider()
        messages = [{"role": "system", "content": system_prompt}] + history
        response_text = await llm.chat(messages)
    except Exception as e:
        response_text = f"Error: {str(e)}"

    # Save assistant response
    history.append({"role": "assistant", "content": response_text})
    session.messages = history
    await db.flush()

    return WorkflowChatResponse(
        session_id=session_id,
        message=response_text,
        role="assistant",
    )


@router.put("/{workflow_id}", response_model=dict)
async def update_workflow(workflow_id: str, data: WorkflowUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workflow).where(Workflow.id == _parse_uuid(workflow_id)))
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")

    update_data = data.model_dump(exclude_none=True)
    # Convert agent_id string to UUID if present
    if "agent_id" in update_data and update_data["agent_id"] is not None:
        update_data["agent_id"] = _parse_uuid(update_data["agent_id"])
    for field, value in update_data.items():
        setattr(wf, field, value)

    await db.flush()
    await db.refresh(wf)
    return _wf_to_dict(wf)


@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workflow).where(Workflow.id == _parse_uuid(workflow_id)))
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    await db.delete(wf)
    await db.flush()
    return {"ok": True}


@router.post("/{workflow_id}/publish", response_model=dict)
async def publish_workflow(workflow_id: str, req: WorkflowPublishRequest, db: AsyncSession = Depends(get_db)):
    """发布或取消发布工作流为公开应用"""
    result = await db.execute(select(Workflow).where(Workflow.id == _parse_uuid(workflow_id)))
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")

    wf.is_public = req.is_public
    await db.flush()
    await db.refresh(wf)
    return _wf_to_dict(wf)


# ── Chat endpoint (runs the workflow AI) ─────────────────────────────────────

@router.post("/{workflow_id}/chat", response_model=WorkflowChatResponse)
async def workflow_chat(
    workflow_id: str,
    req: WorkflowChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """Send a message to the workflow AI and get a response."""
    result = await db.execute(select(Workflow).where(Workflow.id == _parse_uuid(workflow_id)))
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Get or create session
    session_id = req.session_id or str(uuid.uuid4())
    session_uuid = uuid.UUID(session_id)
    workflow_uuid = _parse_uuid(workflow_id)
    session = None
    if req.session_id:
        sess_result = await db.execute(
            select(WorkflowSession).where(WorkflowSession.id == session_uuid)
        )
        session = sess_result.scalar_one_or_none()

    if not session:
        session = WorkflowSession(
            id=session_uuid,
            workflow_id=workflow_uuid,
            messages=[],
        )
        db.add(session)

    # Build message history
    history = session.messages or []
    history.append({"role": "user", "content": req.message})

    # Build system prompt from workflow config
    config = wf.config or {}
    system_prompt = config.get("system_prompt", "You are a helpful AI assistant.")

    # Call LLM
    try:
        llm = get_llm_provider()
        messages = [{"role": "system", "content": system_prompt}] + history
        response_text = await llm.chat(messages)
    except Exception as e:
        response_text = f"Error: {str(e)}"

    # Save assistant response
    history.append({"role": "assistant", "content": response_text})
    session.messages = history
    await db.flush()

    return WorkflowChatResponse(
        session_id=session_id,
        message=response_text,
        role="assistant",
    )
