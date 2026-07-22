from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.db.session import get_db
from app.core.dependencies import require_admin
from app.models.user import User
from app.schemas.admin import (
    AdminCreateUserRequest,
    AdminUpdateUserRequest,
    AdminUserResponse,
    AdminUserListResponse,
    DashboardStats,
    DocumentStats,
    ChatStats,
    UserStats,
)
from app.services.admin_service import AdminService
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/admin", tags=["Admin"])


# ── Dashboard ─────────────────────────────────────────────────────────────

@router.get("/dashboard")
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Full admin dashboard — all stats in one call."""
    result = AnalyticsService(db).get_dashboard_stats()
    return result.model_dump()


# ── Scoped analytics endpoints ────────────────────────────────────────────

@router.get("/documents/stats", response_model=DocumentStats)
def get_document_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Document analytics: counts, storage, file types, upload trends."""
    return AnalyticsService(db).get_document_stats()


@router.get("/users/stats", response_model=UserStats)
def get_user_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """User analytics: totals, roles, most active users."""
    return AnalyticsService(db).get_user_stats()


@router.get("/chat/stats", response_model=ChatStats)
def get_chat_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Chat analytics: conversations, response times, token usage, top questions."""
    return AnalyticsService(db).get_chat_stats()


@router.get("/system/health")
def get_system_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """System health check: database and vector store status."""
    try:
        return AnalyticsService(db).get_system_health()
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))


# ── User management ───────────────────────────────────────────────────────

@router.get("/users", response_model=AdminUserListResponse)
def list_users(
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    service = AdminService(db)
    total, items = service.list_users(search=search, role=role, skip=skip, limit=limit)
    return AdminUserListResponse(
        total=total,
        items=[AdminUserResponse.model_validate(u) for u in items],
    )


@router.post("/users", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: AdminCreateUserRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create any user — admin or employee. Admin only."""
    return AdminUserResponse.model_validate(AdminService(db).create_user(payload))


@router.get("/users/{user_id}", response_model=AdminUserResponse)
def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return AdminUserResponse.model_validate(AdminService(db).get_user(user_id))


@router.patch("/users/{user_id}", response_model=AdminUserResponse)
def update_user(
    user_id: UUID,
    payload: AdminUpdateUserRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return AdminUserResponse.model_validate(AdminService(db).update_user(user_id, payload))


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    AdminService(db).delete_user(user_id, current_user.id)
