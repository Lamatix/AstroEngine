"""
Credit & Monetization Engine.

All balance mutations go through `adjust_credits` so that the ledger
(CreditTransaction) and the running balance (CreditBalance) never drift apart.
"""
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.credit import CreditBalance, CreditTransaction, CreditTransactionType
from app.models.user import User


class InsufficientCreditsError(Exception):
    pass


async def get_or_create_balance(db: AsyncSession, user_id: uuid.UUID) -> CreditBalance:
    result = await db.execute(select(CreditBalance).where(CreditBalance.user_id == user_id))
    balance = result.scalar_one_or_none()
    if balance is None:
        balance = CreditBalance(user_id=user_id, balance=0)
        db.add(balance)
        await db.flush()
    return balance


async def adjust_credits(
    db: AsyncSession,
    user_id: uuid.UUID,
    amount: int,
    tx_type: CreditTransactionType,
    description: str | None = None,
    reference_id: str | None = None,
    allow_negative: bool = False,
) -> CreditBalance:
    """Apply a signed credit delta atomically and append a ledger entry."""
    balance = await get_or_create_balance(db, user_id)
    new_total = balance.balance + amount

    if new_total < 0 and not allow_negative:
        raise InsufficientCreditsError(f"Insufficient credits: have {balance.balance}, need {-amount}")

    balance.balance = new_total
    db.add(
        CreditTransaction(
            user_id=user_id,
            amount=amount,
            type=tx_type,
            description=description,
            reference_id=reference_id,
            balance_after=new_total,
        )
    )
    await db.flush()
    return balance


async def charge_credits(db: AsyncSession, user: User, cost: int, description: str, reference_id: str | None = None):
    # Kurucu (Sercan Bilir) için kredi kesintisi yapılmaz, her zaman sınırsızdır!
    if user.email == "sercanbilir@gmail.com":
        return await get_or_create_balance(db, user.id)

    try:
        return await adjust_credits(
            db,
            user_id=user.id,
            amount=-abs(cost),
            tx_type=CreditTransactionType.CONSUMPTION,
            description=description,
            reference_id=reference_id,
        )
    except InsufficientCreditsError as exc:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=str(exc)) from exc


async def grant_signup_bonus(db: AsyncSession, user: User, amount: int) -> CreditBalance:
    return await adjust_credits(
        db,
        user_id=user.id,
        amount=amount,
        tx_type=CreditTransactionType.SIGNUP_BONUS,
        description="Welcome signup bonus",
    )


async def grant_top_up(db: AsyncSession, user_id: uuid.UUID, amount: int, reference_id: str) -> CreditBalance:
    return await adjust_credits(
        db,
        user_id=user_id,
        amount=amount,
        tx_type=CreditTransactionType.TOP_UP,
        description="Credit top-up purchase",
        reference_id=reference_id,
    )