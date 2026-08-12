from __future__ import annotations

import pytest

from providers.base import BaseProvider, ModelResponse
from router.engine import RelayEngine
from router.policy import RoutingPolicy
from schemas.requests import GenerateRequest


class FakeProvider(BaseProvider):
    """Mock provider for routing tests."""

    def __init__(self, name: str) -> None:
        super().__init__(
            api_key="test-key",
            model="test-model",
        )
        self.name = name
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

        return ModelResponse(
            text=f"{self.name} response",
            provider=self.name,
            model=self.model,
            latency_ms=10.0,
            input_tokens=5,
            output_tokens=5,
            total_tokens=10,
            finish_reason="stop",
        )

    async def health_check(self) -> bool:
        return True


class FakeSettings:
    providers = ["groq", "gemini", "openrouter"]
    max_attempts = 3
    enable_failover = True

    groq_api_key = "test-key"
    gemini_api_key = "test-key"
    openrouter_api_key = "test-key"

    timeout = 30.0


def test_routing_policy_preserves_priority() -> None:
    """Providers should be returned in configured priority order."""

    policy = RoutingPolicy(
        provider_order=("groq", "gemini", "openrouter"),
    )

    result = policy.select_providers(
        ["openrouter", "groq", "gemini"]
    )

    assert result == [
        "groq",
        "gemini",
        "openrouter",
    ]


def test_routing_policy_ignores_unavailable_providers() -> None:
    """Unavailable providers should not be selected."""

    policy = RoutingPolicy(
        provider_order=("groq", "gemini", "openrouter"),
    )

    result = policy.select_providers(
        ["gemini", "openrouter"]
    )

    assert result == [
        "gemini",
        "openrouter",
    ]


def test_routing_policy_respects_max_attempts() -> None:
    """The routing policy should limit provider attempts."""

    policy = RoutingPolicy(
        provider_order=("groq", "gemini", "openrouter"),
        max_attempts=2,
    )

    result = policy.select_providers(
        ["groq", "gemini", "openrouter"]
    )

    assert result == [
        "groq",
        "gemini",
    ]


@pytest.mark.asyncio
async def test_engine_uses_primary_provider() -> None:
    """The engine should use the highest-priority available provider."""

    groq = FakeProvider("groq")
    gemini = FakeProvider("gemini")

    engine = RelayEngine(
        settings=FakeSettings(),
        providers={
            "groq": groq,
            "gemini": gemini,
        },
    )

    result = await engine.generate(
        GenerateRequest(
            prompt="Hello RELAY",
        )
    )

    assert result.provider == "groq"
    assert result.attempts == 1

    assert groq.calls == 1
    assert gemini.calls == 0


@pytest.mark.asyncio
async def test_explicit_provider_selection() -> None:
    """An explicit provider should override the default priority."""

    groq = FakeProvider("groq")
    gemini = FakeProvider("gemini")

    engine = RelayEngine(
        settings=FakeSettings(),
        providers={
            "groq": groq,
            "gemini": gemini,
        },
    )

    result = await engine.generate(
        GenerateRequest(
            prompt="Hello RELAY",
            provider="gemini",
        )
    )

    assert result.provider == "gemini"

    assert groq.calls == 0
    assert gemini.calls == 1


@pytest.mark.asyncio
async def test_unavailable_requested_provider_raises() -> None:
    """An explicitly requested unavailable provider should fail clearly."""

    groq = FakeProvider("groq")

    engine = RelayEngine(
        settings=FakeSettings(),
        providers={
            "groq": groq,
        },
    )

    with pytest.raises(
        ValueError,
        match="Requested provider 'gemini' is not configured",
    ):
        await engine.generate(
            GenerateRequest(
                prompt="Hello RELAY",
                provider="gemini",
            )
        )