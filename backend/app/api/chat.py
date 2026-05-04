"""Chat API routes."""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import ChatRequest, ChatResponse, ConversationOut, MessageOut
from app.agent.engine import AgentEngine
from app.database import get_db
from app.models.conversation import Conversation, Message, MessageRole

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Send a message and get an agent response (non-streaming)."""
    # Get or create conversation
    conversation_id = request.conversation_id or uuid.uuid4()

    if request.conversation_id:
        conversation = await db.get(Conversation, request.conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = Conversation(id=conversation_id, title=request.message[:100])
        if request.agent_id:
            conversation.agent_id = request.agent_id
        db.add(conversation)

    # Save user message
    user_msg = Message(
        conversation_id=conversation_id,
        role=MessageRole.USER,
        content=request.message,
    )
    db.add(user_msg)
    await db.flush()

    # Run agent
    engine = AgentEngine(
        agent_id=str(request.agent_id) if request.agent_id else None,
    )

    # Non-streaming response
    response_content = await engine.run(request.message)

    # Save assistant message
    assistant_msg = Message(
        conversation_id=conversation_id,
        role=MessageRole.ASSISTANT,
        content=response_content,
        token_count=engine.total_tokens,
    )
    db.add(assistant_msg)
    await db.flush()

    return ChatResponse(
        conversation_id=conversation_id,
        message_id=assistant_msg.id,
        content=response_content,
        tokens_used=engine.total_tokens,
    )


@router.post("/stream")
async def chat_stream(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Send a message and get a streaming response."""
    import json
    
    # Get or create conversation
    conversation_id = request.conversation_id or uuid.uuid4()

    if request.conversation_id:
        conversation = await db.get(Conversation, request.conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = Conversation(id=conversation_id, title=request.message[:100])
        if request.agent_id:
            conversation.agent_id = request.agent_id
        db.add(conversation)

    # Save user message
    user_msg = Message(
        conversation_id=conversation_id,
        role=MessageRole.USER,
        content=request.message,
    )
    db.add(user_msg)
    await db.flush()
    await db.commit()

    # Run agent with streaming
    engine = AgentEngine(
        agent_id=str(request.agent_id) if request.agent_id else None,
    )

    async def generate():
        full_response = ""
        try:
            async for chunk in engine.run_stream(request.message):
                full_response += chunk
                yield f"data: {json.dumps({'type': 'text', 'content': chunk})}\n\n"
            
            # Save assistant message after streaming completes
            # Note: This is a simplified version; in production you'd want proper session handling
            yield f"data: {json.dumps({'type': 'done', 'conversation_id': str(conversation_id)})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/conversations", response_model=list[ConversationOut])
async def list_conversations(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List all conversations."""
    from sqlalchemy import select

    stmt = (
        select(Conversation)
        .order_by(Conversation.updated_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    conversations = result.scalars().all()
    return conversations


@router.get("/conversations/{conversation_id}", response_model=ConversationOut)
async def get_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a conversation with messages."""
    conversation = await db.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a conversation."""
    conversation = await db.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await db.delete(conversation)
    return {"status": "deleted"}
