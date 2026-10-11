"""
AI Agent Pipeline - Multi-provider LLM routing layer.

Primary: OpenAI GPT-4o.
Fallback: Google Gemini, used automatically if the primary call fails or times out.
"""
import abc
import logging
from typing import Optional
import httpx
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.models.llm_usage import LLMUsageLog

settings = get_settings()

logger = logging.getLogger("llm_service")


class LLMProviderError(Exception):
    def __init__(self, provider: str, message: str):
        self.provider = provider
        super().__init__(f"[{provider}] {message}")


class LLMResult:
    def __init__(self, provider: str, model: str, output: str, tokens_used: int):
        self.provider = provider
        self.model = model
        self.output = output
        self.tokens_used = tokens_used


class BaseLLMProvider(abc.ABC):
    name: str

    @abc.abstractmethod
    async def generate(self, prompt: str, system_prompt: str | None = None) -> LLMResult:
        ...


class OpenAIProvider(BaseLLMProvider):
    name = "openai"

    @retry(wait=wait_exponential(min=1, max=30), stop=stop_after_attempt(3),
           retry=retry_if_exception_type(httpx.HTTPError), reraise=True)
    async def generate(self, prompt: str, system_prompt: str | None = None) -> LLMResult:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        timeout = getattr(settings, "LLM_REQUEST_TIMEOUT_SECONDS", 30)
        api_key = getattr(settings, "OPENAI_API_KEY", "")
        model_name = getattr(settings, "OPENAI_MODEL", "gpt-4o")

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={"model": model_name, "messages": messages},
                )
                response.raise_for_status()
                data = response.json()
                output = data["choices"][0]["message"]["content"]
                tokens_used = data.get("usage", {}).get("total_tokens", 0)
                return LLMResult(
                    provider=self.name,
                    model=model_name,
                    output=output,
                    tokens_used=tokens_used,
                )
        except (httpx.HTTPError, KeyError, IndexError) as exc:
            raise LLMProviderError(self.name, str(exc)) from exc


class GeminiProvider(BaseLLMProvider):
    name = "gemini"

    @retry(wait=wait_exponential(min=1, max=30), stop=stop_after_attempt(3),
           retry=retry_if_exception_type(httpx.HTTPError), reraise=True)
    async def generate(self, prompt: str, system_prompt: str | None = None) -> LLMResult:
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        timeout = getattr(settings, "LLM_REQUEST_TIMEOUT_SECONDS", 30)
        api_key = getattr(settings, "GEMINI_API_KEY", "")
        model_name = getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash")

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model_name}:generateContent?key={api_key}"
        )
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    url,
                    json={"contents": [{"parts": [{"text": full_prompt}]}]},
                )
                response.raise_for_status()
                data = response.json()
                output = data["candidates"][0]["content"]["parts"][0]["text"]
                tokens_used = data.get("usageMetadata", {}).get("totalTokenCount", 0)
                return LLMResult(
                    provider=self.name,
                    model=model_name,
                    output=output,
                    tokens_used=tokens_used,
                )
        except (httpx.HTTPError, KeyError, IndexError) as exc:
            raise LLMProviderError(self.name, str(exc)) from exc


class LLMRouter:
    """Routes a generation request to the preferred provider, falling back on failure."""

    def __init__(self):
        self.providers: dict[str, BaseLLMProvider] = {
            "openai": OpenAIProvider(),
            "gemini": GeminiProvider(),
        }
        self.default_order = ["openai", "gemini"]

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        preferred_provider: str | None = None,
        db: AsyncSession | None = None,
        user_id: str | None = None,
    ) -> LLMResult:
        order = self.default_order
        if preferred_provider and preferred_provider in self.providers:
            order = [preferred_provider] + [
                p for p in self.default_order if p != preferred_provider
            ]

        last_error: Exception | None = None
        for provider_name in order:
            provider = self.providers[provider_name]
            try:
                logger.info("Attempting LLM generation via provider=%s", provider_name)
                result = await provider.generate(prompt, system_prompt)

                # Opsiyonel: Veritabanına LLM kullanım kaydı düşer
                if db and user_id:
                    try:
                        log_entry = LLMUsageLog(
                            user_id=user_id,
                            model_name=result.model,
                            total_tokens=result.tokens_used,
                        )
                        db.add(log_entry)
                        await db.commit()
                    except Exception as db_exc:
                        logger.error("LLM usage log DB save error: %s", db_exc)

                return result
            except LLMProviderError as exc:
                logger.warning("Provider %s failed: %s", provider_name, exc)
                last_error = exc
                continue

        raise LLMProviderError("router", f"All providers failed. Last error: {last_error}")


llm_router = LLMRouter()
