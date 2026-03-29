from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
import uuid

from app.models.user import PlanType


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    api_key: str
    plan: PlanType
    is_active: bool
    balance: float
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[str] = None
