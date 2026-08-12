from __future__ import annotations

import pytest

from providers.base import BaseProvider, ModelResponse
from router.engine import RelayEngine
from schemas.requests import GenerateRequest


class FakeProvider(BaseProvider):
    """Mock provider used for testing RELAY without real API calls."""

    def __init__(
        self,
        name: str,
        *,
        response: str = "Success",
        should_fail: bool = False,
    ) -> None:
        super().__init__(
            api_key="test-key",
            model="test-model",
        )

        self.name = name
        self.response = response
        self.should_fail = should_fail
        self.calls = 0

    async def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> ModelResponse:
        self.calls += 1

        if self.should_fail:
            raise TimeoutError(f"{self.name} timed out")

        return ModelResponse(
            text=self.response,
            provider=self.name,
            model=self.model,
            latency_ms=10.0,
            input_tokens=5,
            output_tokens=5,
            total_tokens=10,
            finish_reason="stop",
        )

    async def health_check(self) -> bool:
        return not self.should_fail


class FakeSettings:
    """Minimal settings object for isolated router tests."""

    providers = ["groq", "gemini", "openrouter"]
    max_attempts = 3
    enable_failover = True

    groq_api_key = "test-key"
    gemini_api_key = "test-key"
    openrouter_api_key = "test-key"

    timeout = 30.0


@pytest.mark.asyncio
async def test_primary_provider_success() -> None:
    """RELAY should return the primary provider response."""

    groq = FakeProvider(
        "groq",
        response="Groq response",
    )

    gemini = FakeProvider(
        "gemini",
        response="Gemini response",
    )

    engine = RelayEngine(
        settings=FakeSettings(),
        providers={
            "groq": groq,
            "gemini": gemini,
        },
    )

    request = GenerateRequest(
        prompt="Hello RELAY",
    )

    result = await engine.generate(request)

    assert result.text == "Groq response"
    assert result.provider == "groq"
    assert result.attempts == 1
    assert result.fallback_used is False

    assert groq.calls == 1
    assert gemini.calls == 0


@pytest.mark.asyncio
async def test_failover_to_second_provider() -> None:
    """RELAY should fail over when the primary provider fails."""

    groq = FakeProvider(
        "groq",
        should_fail=True,
    )

    gemini = FakeProvider(
        "gemini",
        response="Gemini response",
    )

    engine = RelayEngine(
        settings=FakeSettings(),
        providers={
            "groq": groq,
            "gemini": gemini,
        },
    )

    request = GenerateRequest(
        prompt="Hello RELAY",
    )

    result = await engine.generate(request)

    assert result.text == "Gemini response"
    assert result.provider == "gemini"
    assert result.attempts == 2
    assert result.fallback_used is True

    assert groq.calls == 1
    assert gemini.calls == 1


@pytest.mark.asyncio
async def test_failover_to_third_provider() -> None:
    """RELAY should continue to the third provider when needed."""

    groq = FakeProvider(
        "groq",
        should_fail=True,
    )

    gemini = FakeProvider(
        "gemini",
        should_fail=True,
    )

    openrouter = FakeProvider(
        "openrouter",
        response="OpenRouter response",
    )

    engine = RelayEngine(
        settings=FakeSettings(),
        providers={
            "groq": groq,
            "gemini": gemini,
            "openrouter": openrouter,
        },
    )

    request = GenerateRequest(
        prompt="Hello RELAY",
    )

    result = await engine.generate(request)

    assert result.text == "OpenRouter response"
    assert result.provider == "openrouter"
    assert result.attempts == 3
    assert result.fallback_used is True

    assert groq.calls == 1
    assert gemini.calls == 1
    assert openrouter.calls == 1


@pytest.mark.asyncio
async def test_all_providers_fail() -> None:
    """RELAY should raise when every provider fails."""

    groq = FakeProvider(
        "groq",
        should_fail=True,
    )

    gemini = FakeProvider(
        "gemini",
        should_fail=True,
    )

    openrouter = FakeProvider(
        "openrouter",
        should_fail=True,
    )

    engine = RelayEngine(
        settings=FakeSettings(),
        providers={
            "groq": groq,
            "gemini": gemini,
            "openrouter": openrouter,
        },
    )

    request = GenerateRequest(
        prompt="Hello RELAY",
    )

    with pytest.raises(RuntimeError, match="All RELAY providers failed"):
        await engine.generate(request)

    assert groq.calls == 1
    assert gemini.calls == 1
    assert openrouter.calls == 1