from pydantic import BaseModel, Field


class LLMGenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)
    system_prompt: str | None = None
    preferred_provider: str | None = Field(default=None, description="'openai' or 'gemini'")


class LLMGenerateResponse(BaseModel):
    provider_used: str
    model: str
    output: str
    tokens_used: int
    credits_charged: int
