from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserResponse,
    UserUpdateRequest,
)
from app.services.auth_service import AuthService
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    """
    Public registration endpoint.
    Role is always forced to 'employee' on self-registration.
    Admins are created by other admins via /admin/users.
    """
    service = AuthService(db)
    user = service.register(payload, requester_role=None)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLoginRequest, db: Session = Depends(get_db)):
    """Returns JWT access + refresh tokens."""
    service = AuthService(db)
    return service.login(payload)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Exchange a valid refresh token for a new token pair."""
    service = AuthService(db)
    return service.refresh(payload.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(current_user: User = Depends(get_current_user)):
    """
    Stateless JWT logout — client discards tokens.
    Token blacklisting can be added in a future milestone via Redis.
    """
    return None


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Returns the currently authenticated user's profile."""
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_me(
    payload: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update own profile (name or email)."""
    if payload.full_name:
        current_user.full_name = payload.full_name
    if payload.email:
        # check email not taken by another user
        from app.models.user import User as UserModel
        existing = db.query(UserModel).filter(
            UserModel.email == payload.email,
            UserModel.id != current_user.id,
        ).first()
        if existing:
            from fastapi import HTTPException
            raise HTTPException(status_code=409, detail="Email already in use")
        current_user.email = payload.email

    db.commit()
    db.refresh(current_user)
    return current_user
