from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.chat import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatSessionListResponse,
    ChatMessageResponse,
    ChatMessageListResponse,
    AskQuestionRequest,
    AskQuestionResponse,
    SourceCitation,
)
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: ChatSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start a new conversation session."""
    service = ChatService(db)
    return ChatSessionResponse.model_validate(
        service.create_session(current_user, payload.title)
    )


@router.get("/sessions", response_model=ChatSessionListResponse)
def list_sessions(
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all sessions for the current user, newest first."""
    service = ChatService(db)
    total, items = service.list_sessions(current_user, search=search, skip=skip, limit=limit)
    return ChatSessionListResponse(
        total=total,
        items=[ChatSessionResponse.model_validate(s) for s in items],
    )


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
def get_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ChatService(db)
    return ChatSessionResponse.model_validate(service.get_session(session_id, current_user))


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a conversation and all its messages."""
    ChatService(db).delete_session(session_id, current_user)


@router.post("/sessions/{session_id}/messages", response_model=AskQuestionResponse)
def ask_question(
    session_id: UUID,
    payload: AskQuestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send a question — triggers full RAG pipeline.
    Returns AI answer + source citations.
    """
    service = ChatService(db)
    assistant_msg, sources = service.ask(
        session_id=session_id,
        question=payload.question,
        user=current_user,
        top_k=payload.top_k,
    )

    return AskQuestionResponse(
        message=_format_message(assistant_msg, sources),
        sources=sources,
    )


@router.get("/sessions/{session_id}/messages", response_model=ChatMessageListResponse)
def get_messages(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve full message history for a session."""
    service = ChatService(db)
    total, messages = service.list_messages(session_id, current_user)

    formatted = []
    for msg in messages:
        sources = _parse_sources(msg.source_chunks)
        formatted.append(_format_message(msg, sources))

    return ChatMessageListResponse(total=total, items=formatted)


# ── Helpers ──────────────────────────────────────────────────────────────

def _parse_sources(source_chunks) -> list:
    if not source_chunks:
        return []
    return [
        SourceCitation(
            chunk_id=s.get("chunk_id", ""),
            document_name=s.get("document_name", ""),
            page_number=s.get("page_number"),
            section_heading=s.get("section_heading"),
            score=s.get("score", 0.0),
        )
        for s in source_chunks
    ]


def _format_message(msg, sources: list) -> ChatMessageResponse:
    return ChatMessageResponse(
        id=msg.id,
        session_id=msg.session_id,
        role=msg.role,
        content=msg.content,
        sources=sources if msg.role.value == "assistant" else None,
        response_time_ms=msg.response_time_ms,
        created_at=msg.created_at,
    )
