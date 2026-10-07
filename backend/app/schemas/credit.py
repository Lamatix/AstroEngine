import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.credit import CreditTransactionType, TopUpStatus


class CreditBalanceRead(BaseModel):
    balance: int
    updated_at: datetime

    model_config = {"from_attributes": True}


class CreditTransactionRead(BaseModel):
    id: uuid.UUID
    amount: int
    type: CreditTransactionType
    description: str | None
    balance_after: int
    created_at: datetime

    model_config = {"from_attributes": True}


class TopUpCreateRequest(BaseModel):
    package_id: str = Field(description="Identifier of a predefined credit package, e.g. 'starter_100'")


class TopUpCheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str


class TopUpTransactionRead(BaseModel):
    id: uuid.UUID
    amount_usd: float
    credits_purchased: int
    status: TopUpStatus
    created_at: datetime

    model_config = {"from_attributes": True}
