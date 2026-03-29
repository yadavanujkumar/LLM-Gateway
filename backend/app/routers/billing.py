from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.middleware.auth import get_current_user
from app.services.billing import create_payment_intent, handle_webhook, add_balance
from app.services.auth import get_user_by_id
import uuid

router = APIRouter(prefix="/billing", tags=["Billing"])


@router.post("/create-payment-intent")
async def payment_intent(
    amount: float,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a Stripe payment intent to add balance."""
    if amount <= 0 or amount > 1000:
        raise HTTPException(status_code=400, detail="Amount must be between 0 and 1000 USD")
    return create_payment_intent(db, current_user, amount)


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(alias="stripe-signature"),
    db: Session = Depends(get_db),
):
    """Handle Stripe webhook events."""
    payload = await request.body()
    try:
        event = handle_webhook(payload, stripe_signature)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        user_id_str = payment_intent.get("metadata", {}).get("user_id")
        if user_id_str:
            user = get_user_by_id(db, uuid.UUID(user_id_str))
            if user:
                amount_usd = payment_intent["amount"] / 100
                add_balance(db, user, amount_usd)

    return {"status": "ok"}


@router.get("/balance")
async def get_balance(current_user: User = Depends(get_current_user)):
    """Get current user balance."""
    return {"balance": current_user.balance, "currency": "USD"}
