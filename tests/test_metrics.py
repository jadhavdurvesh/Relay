from __future__ import annotations

from telemetry.metrics import MetricsCollector


def test_record_success() -> None:
    """A successful request should be recorded correctly."""

    metrics = MetricsCollector()

    metric = metrics.record_success(
        provider="groq",
        model="test-model",
        latency_ms=120.5,
        input_tokens=20,
        output_tokens=30,
        total_tokens=50,
        attempts=1,
        fallback_used=False,
    )

    assert metric.success is True
    assert metric.provider == "groq"
    assert metric.model == "test-model"
    assert metric.latency_ms == 120.5
    assert metric.total_tokens == 50

    assert metrics.count() == 1


def test_record_failure() -> None:
    """A failed request should be recorded correctly."""

    metrics = MetricsCollector()

    error = TimeoutError("provider timed out")

    metric = metrics.record_failure(
        provider="groq",
        model="test-model",
        error=error,
        attempts=1,
    )

    assert metric.success is False
    assert metric.provider == "groq"
    assert metric.error_type == "TimeoutError"
    assert metric.error_message == "provider timed out"

    assert metrics.count() == 1


def test_summary() -> None:
    """Summary should correctly aggregate request statistics."""

    metrics = MetricsCollector()

    metrics.record_success(
        provider="groq",
        model="test-model",
        latency_ms=100,
        total_tokens=50,
    )

    metrics.record_success(
        provider="gemini",
        model="test-model",
        latency_ms=200,
        total_tokens=100,
        attempts=2,
        fallback_used=True,
    )

    metrics.record_failure(
        provider="openrouter",
        model="test-model",
        error=RuntimeError("test failure"),
    )

    summary = metrics.summary()

    assert summary["total_requests"] == 3
    assert summary["successful_requests"] == 2
    assert summary["failed_requests"] == 1
    assert summary["success_rate"] == 2 / 3
    assert summary["average_latency_ms"] == 150
    assert summary["total_tokens"] == 150
    assert summary["fallback_requests"] == 1


def test_provider_stats() -> None:
    """Provider statistics should be grouped correctly."""

    metrics = MetricsCollector()

    metrics.record_success(
        provider="groq",
        model="test-model",
    )

    metrics.record_success(
        provider="groq",
        model="test-model",
        fallback_used=True,
    )

    metrics.record_failure(
        provider="gemini",
        model="test-model",
        error=RuntimeError("failure"),
    )

    stats = metrics.provider_stats()

    assert stats["groq"]["requests"] == 2
    assert stats["groq"]["successes"] == 2
    assert stats["groq"]["failures"] == 0
    assert stats["groq"]["fallbacks"] == 1

    assert stats["gemini"]["requests"] == 1
    assert stats["gemini"]["successes"] == 0
    assert stats["gemini"]["failures"] == 1


def test_clear() -> None:
    """Clearing telemetry should remove all recorded metrics."""

    metrics = MetricsCollector()

    metrics.record_success(
        provider="groq",
        model="test-model",
    )

    assert metrics.count() == 1

    metrics.clear()

    assert metrics.count() == 0
    assert metrics.summary()["total_requests"] == 0