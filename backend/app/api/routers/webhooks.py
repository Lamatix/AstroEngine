import logging
import uuid

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.credit import TopUpStatus, TopUpTransaction
from app.services.credit_service import grant_top_up
from app.services.stripe_service import get_package, verify_webhook_event

logger = logging.getLogger("webhooks")
router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/stripe", status_code=status.HTTP_200_OK)
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = verify_webhook_event(payload, sig_header)
    except (ValueError, stripe.error.SignatureVerificationError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook signature") from exc

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = session.get("metadata", {})
        user_id = metadata.get("user_id")
        package_id = metadata.get("package_id")

        if not user_id or not package_id:
            logger.error("Stripe checkout session missing metadata: %s", session.get("id"))
            return {"received": True}

        existing = await db.execute(
            select(TopUpTransaction).where(TopUpTransaction.stripe_session_id == session["id"])
        )
        if existing.scalar_one_or_none() is not None:
            return {"received": True}  # idempotent: already processed

        package = get_package(package_id)
        user_uuid = uuid.UUID(user_id)
        top_up = TopUpTransaction(
            user_id=user_uuid,
            stripe_session_id=session["id"],
            stripe_payment_intent_id=session.get("payment_intent"),
            amount_usd=package["price_usd"],
            credits_purchased=package["credits"],
            status=TopUpStatus.SUCCEEDED,
        )
        db.add(top_up)
        await grant_top_up(db, user_id=user_uuid, amount=package["credits"], reference_id=session["id"])
        await db.commit()

    return {"received": True}
