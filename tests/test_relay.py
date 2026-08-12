from __future__ import annotations

import pytest

from main import Relay
from providers.base import BaseProvider, ModelResponse


class FakeProvider(BaseProvider):
    """Mock provider for testing the public Relay interface."""

    def __init__(
        self,
        name: str,
        *,
        should_fail: bool = False,
        response: str = "Success",
    ) -> None:
        super().__init__(
            api_key="test-key",
            model="test-model",
        )

        self.name = name
        self.should_fail = should_fail
        self.response = response
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
            latency_ms=25.0,
            input_tokens=5,
            output_tokens=10,
            total_tokens=15,
            finish_reason="stop",
        )

    async def health_check(self) -> bool:
        return not self.should_fail


class FakeSettings:
    providers = ["groq", "gemini", "openrouter"]
    max_attempts = 3
    enable_failover = True

    groq_api_key = "test-key"
    gemini_api_key = "test-key"
    openrouter_api_key = "test-key"

    timeout = 30.0


@pytest.mark.asyncio
async def test_relay_shares_telemetry_with_engine() -> None:
    """Relay and its engine should use the same metrics collector."""

    from telemetry.metrics import MetricsCollector

    metrics = MetricsCollector()

    relay = Relay(
        settings=FakeSettings(),
        metrics=metrics,
    )

    assert relay.metrics is relay.engine.metrics


@pytest.mark.asyncio
async def test_relay_records_failover_attempts() -> None:
    """Relay telemetry should contain both failed and successful attempts."""

    from router.engine import RelayEngine

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

    relay = Relay(
        settings=FakeSettings(),
        engine=engine,
    )

    result = await relay.generate("Hello RELAY")

    assert result.provider == "gemini"
    assert result.fallback_used is True
    assert result.attempts == 2

    metrics = relay.metrics.all()

    assert len(metrics) == 2

    assert metrics[0].provider == "groq"
    assert metrics[0].success is False
    assert metrics[0].fallback_used is False

    assert metrics[1].provider == "gemini"
    assert metrics[1].success is True
    assert metrics[1].fallback_used is True


@pytest.mark.asyncio
async def test_relay_metrics_summary() -> None:
    """Relay should expose the engine's telemetry summary."""

    from router.engine import RelayEngine

    groq = FakeProvider(
        "groq",
        response="Groq response",
    )

    engine = RelayEngine(
        settings=FakeSettings(),
        providers={
            "groq": groq,
        },
    )

    relay = Relay(
        settings=FakeSettings(),
        engine=engine,
    )

    await relay.generate("Hello RELAY")

    summary = relay.metrics_summary()

    assert summary["total_requests"] == 1
    assert summary["successful_requests"] == 1
    assert summary["failed_requests"] == 0
    assert summary["total_tokens"] == 15