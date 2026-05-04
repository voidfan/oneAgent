import os

# ── 1. backend/app/api/workflows.py ──────────────────────────────────────────
workflows_api = r'''"""Workflow API - CRUD for Puck-based workflow designer."""
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
    puck_data: Optional[dict] = None
    agent_id: Optional[str] = None
    config: Optional[dict] = None
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None


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
        agent_id=data.agent_id,
        config=data.config or {},
        is_public=data.is_public,
    )
    db.add(wf)
    await db.commit()
    await db.refresh(wf)
    return _wf_to_dict(wf)


@router.get("/{workflow_id}", response_model=dict)
async def get_workflow(workflow_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
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


@router.put("/{workflow_id}", response_model=dict)
async def update_workflow(workflow_id: str, data: WorkflowUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(wf, field, value)

    await db.commit()
    await db.refresh(wf)
    return _wf_to_dict(wf)


@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    await db.delete(wf)
    await db.commit()
    return {"ok": True}


# ── Chat endpoint (runs the workflow AI) ─────────────────────────────────────

@router.post("/{workflow_id}/chat", response_model=WorkflowChatResponse)
async def workflow_chat(
    workflow_id: str,
    req: WorkflowChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """Send a message to the workflow AI and get a response."""
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Get or create session
    session_id = req.session_id or str(uuid.uuid4())
    session = None
    if req.session_id:
        sess_result = await db.execute(
            select(WorkflowSession).where(WorkflowSession.id == req.session_id)
        )
        session = sess_result.scalar_one_or_none()

    if not session:
        session = WorkflowSession(
            id=session_id,
            workflow_id=workflow_id,
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
    await db.commit()

    return WorkflowChatResponse(
        session_id=session_id,
        message=response_text,
        role="assistant",
    )
'''

# ── 2. backend/app/models/workflow.py (also add back_populates to Agent) ─────
# We already wrote this file, just need to add workflows relationship to Agent

# ── 3. frontend/src/services/api.js additions (workflow API) ─────────────────
workflow_api_addition = r'''
// ── Workflow API ──────────────────────────────────────────────────────────────
export const workflowAPI = {
  list: () => api.get('/api/workflows').then(r => r.data),
  get: (id) => api.get(`/api/workflows/${id}`).then(r => r.data),
  getBySlug: (slug) => api.get(`/api/workflows/by-slug/${slug}`).then(r => r.data),
  create: (data) => api.post('/api/workflows', data).then(r => r.data),
  update: (id, data) => api.put(`/api/workflows/${id}`, data).then(r => r.data),
  delete: (id) => api.delete(`/api/workflows/${id}`).then(r => r.data),
  chat: (id, data) => api.post(`/api/workflows/${id}/chat`, data).then(r => r.data),
};
'''

# Write backend API
with open('backend/app/api/workflows.py', 'w', encoding='utf-8') as f:
    f.write(workflows_api)
print('wrote backend/app/api/workflows.py')

# Append workflowAPI to frontend/src/services/api.js
with open('frontend/src/services/api.js', 'r', encoding='utf-8') as f:
    api_content = f.read()

if 'workflowAPI' not in api_content:
    with open('frontend/src/services/api.js', 'a', encoding='utf-8') as f:
        f.write('\n' + workflow_api_addition)
    print('appended workflowAPI to frontend/src/services/api.js')
else:
    print('workflowAPI already exists in api.js')

print('done')
