from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user
from app.database import get_db
from app.models.credit import CreditTransaction
from app.models.user import User
from app.schemas.credit import (
    CreditBalanceRead,
    CreditTransactionRead,
    TopUpCheckoutResponse,
    TopUpCreateRequest,
)
from app.services.credit_service import get_or_create_balance
from app.services.stripe_service import create_checkout_session

router = APIRouter(prefix="/credits", tags=["Credits"])


@router.get("/balance", response_model=CreditBalanceRead)
async def get_balance(user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    balance = await get_or_create_balance(db, user.id)
    await db.commit()
    return balance


@router.get("/transactions", response_model=list[CreditTransactionRead])
async def list_transactions(
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
):
    result = await db.execute(
        select(CreditTransaction)
        .where(CreditTransaction.user_id == user.id)
        .order_by(CreditTransaction.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.post("/top-up/checkout", response_model=TopUpCheckoutResponse)
async def create_top_up_checkout(payload: TopUpCreateRequest, user: User = Depends(get_current_active_user)):
    try:
        session = create_checkout_session(
            user_id=str(user.id),
            package_id=payload.package_id,
            success_url="http://localhost:3000/dashboard?checkout=success",
            cancel_url="http://localhost:3000/dashboard?checkout=canceled",
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return TopUpCheckoutResponse(checkout_url=session.url, session_id=session.id)
