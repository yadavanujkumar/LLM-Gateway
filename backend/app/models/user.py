import uuid
import secrets
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class PlanType(str, enum.Enum):
    free = "free"
    starter = "starter"
    pro = "pro"
    enterprise = "enterprise"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    api_key = Column(String(64), unique=True, nullable=False, index=True,
                     default=lambda: f"sk-{secrets.token_urlsafe(40)}")
    plan = Column(Enum(PlanType), default=PlanType.free, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    stripe_customer_id = Column(String(255), nullable=True)
    balance = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    usages = relationship("Usage", back_populates="user", lazy="dynamic")
    logs = relationship("RequestLog", back_populates="user", lazy="dynamic")
