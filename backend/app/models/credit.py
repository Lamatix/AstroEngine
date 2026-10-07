import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CreditTransactionType(str, enum.Enum):
    SIGNUP_BONUS = "signup_bonus"
    TOP_UP = "top_up"
    CONSUMPTION = "consumption"
    REFUND = "refund"
    ADMIN_ADJUSTMENT = "admin_adjustment"


class TopUpStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


class CreditBalance(Base):
    __tablename__ = "credit_balances"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="credit_balance")


class CreditTransaction(Base):
    """Immutable ledger of every credit movement (consumption, bonus, refund)."""

    __tablename__ = "credit_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # positive=credit, negative=debit
    type: Mapped[CreditTransactionType] = mapped_column(Enum(CreditTransactionType), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    reference_id: Mapped[str] = mapped_column(String(255), nullable=True)  # e.g. video_job_id, stripe_payment_id
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TopUpTransaction(Base):
    """Records Stripe payment top-ups."""

    __tablename__ = "top_up_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    stripe_session_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=True)
    stripe_payment_intent_id: Mapped[str] = mapped_column(String(255), nullable=True)
    amount_usd: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    credits_purchased: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[TopUpStatus] = mapped_column(Enum(TopUpStatus), default=TopUpStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
