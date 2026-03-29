import stripe
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User

stripe.api_key = settings.STRIPE_SECRET_KEY


def get_or_create_customer(db: Session, user: User) -> str:
    if user.stripe_customer_id:
        return user.stripe_customer_id

    customer = stripe.Customer.create(
        email=user.email,
        metadata={"user_id": str(user.id)},
    )
    user.stripe_customer_id = customer.id
    db.commit()
    return customer.id


def add_balance(db: Session, user: User, amount_usd: float) -> User:
    """Add balance to user account after successful payment."""
    user.balance += amount_usd
    db.commit()
    db.refresh(user)
    return user


def deduct_balance(db: Session, user: User, cost: float) -> bool:
    """Deduct cost from user balance. Returns False if insufficient funds."""
    if user.balance < cost and user.plan == "free":
        # Free tier users must have balance for paid requests
        return False
    user.balance -= cost
    db.commit()
    return True


def create_payment_intent(db: Session, user: User, amount_usd: float) -> dict:
    customer_id = get_or_create_customer(db, user)
    intent = stripe.PaymentIntent.create(
        amount=int(amount_usd * 100),  # cents
        currency="usd",
        customer=customer_id,
        metadata={"user_id": str(user.id)},
    )
    return {"client_secret": intent.client_secret, "amount": amount_usd}


def handle_webhook(payload: bytes, sig_header: str) -> dict:
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        raise ValueError(f"Webhook error: {e}")

    return {"type": event["type"], "data": event["data"]}
