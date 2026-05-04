"""Agent management API routes."""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import AgentCreate, AgentUpdate, AgentOut, ExecutionOut
from app.database import get_db
from app.models.agent import Agent, AgentExecution

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.post("/", response_model=AgentOut)
async def create_agent(data: AgentCreate, db: AsyncSession = Depends(get_db)):
    """Create a new agent."""
    agent = Agent(
        name=data.name,
        description=data.description,
        system_prompt=data.system_prompt,
        llm_provider=data.llm_provider,
        llm_model=data.llm_model,
        max_steps=data.max_steps,
        temperature=data.temperature,
        tools_config=data.tools_config,
    )
    db.add(agent)
    await db.flush()
    await db.refresh(agent)
    return agent


@router.get("/", response_model=list[AgentOut])
async def list_agents(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List all agents."""
    stmt = select(Agent).order_by(Agent.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{agent_id}", response_model=AgentOut)
async def get_agent(agent_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get agent details."""
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.put("/{agent_id}", response_model=AgentOut)
async def update_agent(
    agent_id: uuid.UUID,
    data: AgentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an agent."""
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(agent, key, value)

    await db.flush()
    await db.refresh(agent)
    return agent


@router.delete("/{agent_id}")
async def delete_agent(agent_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Delete an agent."""
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    await db.delete(agent)
    return {"status": "deleted"}


@router.get("/{agent_id}/executions", response_model=list[ExecutionOut])
async def list_executions(
    agent_id: uuid.UUID,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """List executions for an agent."""
    stmt = (
        select(AgentExecution)
        .where(AgentExecution.agent_id == agent_id)
        .order_by(AgentExecution.started_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()
