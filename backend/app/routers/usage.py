from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.usage import Usage
from app.models.log import RequestLog
from app.schemas.usage import UsageResponse, UsageSummary, UsageRecord, LogRecord
from app.middleware.auth import get_current_user
from app.services.usage import get_usage_summary

router = APIRouter(tags=["Usage"])


@router.get("/v1/usage", response_model=UsageResponse)
async def get_usage(
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get usage statistics for the current user."""
    summary_data = get_usage_summary(db, current_user.id, start_date, end_date)

    query = db.query(Usage).filter(Usage.user_id == current_user.id)
    if start_date:
        query = query.filter(Usage.timestamp >= start_date)
    if end_date:
        query = query.filter(Usage.timestamp <= end_date)

    total = query.count()
    records = (
        query.order_by(Usage.timestamp.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return UsageResponse(
        summary=UsageSummary(**summary_data),
        records=[UsageRecord.model_validate(r) for r in records],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/v1/logs")
async def get_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get request logs for the current user."""
    query = db.query(RequestLog).filter(RequestLog.user_id == current_user.id)
    total = query.count()
    logs = (
        query.order_by(RequestLog.timestamp.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "records": [LogRecord.model_validate(log) for log in logs],
        "page": page,
        "page_size": page_size,
        "total": total,
    }
