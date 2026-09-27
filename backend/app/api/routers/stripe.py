import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Header, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.credit import CreditBalance, CreditTransaction, TopUpTransaction
from app.core.deps import get_current_active_user
from app.services.stripe_service import (
    create_checkout_session,
    verify_webhook_event,
    CREDIT_PACKAGES,
)

logger = logging.getLogger("stripe_router")
router = APIRouter(prefix="/stripe", tags=["Stripe & Payments"])


class CreateCheckoutRequest(BaseModel):
    package_id: str = Field(..., example="starter_100", description="starter_100, growth_500, pro_1500")
    success_url: str = Field(..., example="https://app.example.com/payment/success")
    cancel_url: str = Field(..., example="https://app.example.com/payment/cancel")


@router.get("/packages")
async def list_packages():
    """Mevcut kredi paketlerini listeler."""
    return {"packages": CREDIT_PACKAGES}


@router.post("/create-checkout-session")
async def handle_create_checkout(
    payload: CreateCheckoutRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Kullanıcı için paket seçimli Stripe satın alma oturumu başlatır."""
    try:
        session = create_checkout_session(
            user_id=str(current_user.id),
            package_id=payload.package_id,
            success_url=payload.success_url,
            cancel_url=payload.cancel_url,
        )
        return {"checkout_url": session.url, "session_id": session.id}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.error("Stripe session creation failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
    db: AsyncSession = Depends(get_db),
):
    """Stripe webhook bildirimlerini işler ve bakiyeleri aktarır."""
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    payload = await request.body()

    try:
        event = verify_webhook_event(payload, stripe_signature)
    except Exception as exc:
        logger.error("Webhook verification failed: %s", exc)
        raise HTTPException(status_code=400, detail=f"Webhook Error: {str(exc)}")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = session.get("metadata", {})

        user_id = metadata.get("user_id")
        package_id = metadata.get("package_id")
        credits_added = int(metadata.get("credits", 0))
        payment_intent_id = session.get("payment_intent")
        amount_paid = session.get("amount_total", 0) / 100.0

        if user_id and credits_added > 0:
            stmt = select(CreditBalance).where(CreditBalance.user_id == user_id)
            res = await db.execute(stmt)
            balance = res.scalar_one_or_none()

            if not balance:
                balance = CreditBalance(user_id=user_id, balance=credits_added)
                db.add(balance)
            else:
                balance.balance += credits_added

            tx = CreditTransaction(
                user_id=user_id,
                amount=credits_added,
                type="TOPUP",
                description=f"Stripe Top-Up ({package_id}): +{credits_added} credits",
            )
            db.add(tx)

            topup = TopUpTransaction(
                user_id=user_id,
                amount_paid=amount_paid,
                credits_added=credits_added,
                payment_provider="stripe",
                reference_id=payment_intent_id,
            )
            db.add(topup)

            await db.commit()
            logger.info("Successfully added %d credits to user %s", credits_added, user_id)

    return {"status": "success"}