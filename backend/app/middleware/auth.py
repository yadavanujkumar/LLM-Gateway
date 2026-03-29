from typing import Optional
from fastapi import HTTPException, Security, Depends, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.services.auth import get_user_by_api_key, decode_token, get_user_by_id
import uuid

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


def get_api_key(authorization: Optional[str] = Security(api_key_header)) -> Optional[str]:
    if authorization and authorization.startswith("Bearer sk-"):
        return authorization[7:]  # strip "Bearer "
    if authorization and authorization.startswith("sk-"):
        return authorization
    return None


async def get_current_user(
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Check if it's an API key (starts with sk-)
    if token.startswith("sk-"):
        user = get_user_by_api_key(db, token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled",
            )
        return user

    # Otherwise treat as JWT token
    token_data = decode_token(token)
    user = get_user_by_id(db, uuid.UUID(token_data.user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )
    return user
