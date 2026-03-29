from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.services.auth import create_user, authenticate_user, create_access_token, regenerate_api_key
from app.middleware.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """Register a new user and get an API key."""
    user = create_user(db, user_in)
    return user


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login and receive a JWT access token."""
    user = authenticate_user(db, credentials.email, credentials.password)
    access_token = create_access_token({"sub": str(user.id)})
    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user profile."""
    return current_user


@router.post("/regenerate-key", response_model=UserResponse)
async def regenerate_key(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Regenerate API key."""
    return regenerate_api_key(db, current_user)
