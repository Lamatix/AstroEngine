from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.core.deps import get_current_active_user
from app.database import get_db
from app.models.llm_usage import LLMUsageLog
from app.models.user import User
from app.schemas.llm import LLMGenerateRequest, LLMGenerateResponse
from app.services.credit_service import charge_credits
from app.services.llm_service import LLMProviderError, llm_router

router = APIRouter(prefix="/llm", tags=["AI Agent Pipeline"])
settings = get_settings()


@router.post("/generate", response_model=LLMGenerateResponse)
async def generate(
    payload: LLMGenerateRequest,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    cost = settings.CREDIT_COST_LLM_REQUEST
    await charge_credits(db, user, cost, description="LLM generation request")

    try:
        result = await llm_router.generate(
            prompt=payload.prompt,
            system_prompt=payload.system_prompt,
            preferred_provider=payload.preferred_provider,
        )
    except LLMProviderError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    db.add(
        LLMUsageLog(
            user_id=user.id,
            provider=result.provider,
            model=result.model,
            prompt=payload.prompt,
            response_excerpt=result.output[:500],
            tokens_used=result.tokens_used,
            credits_charged=cost,
        )
    )
    await db.commit()

    return LLMGenerateResponse(
        provider_used=result.provider,
        model=result.model,
        output=result.output,
        tokens_used=result.tokens_used,
        credits_charged=cost,
    )
