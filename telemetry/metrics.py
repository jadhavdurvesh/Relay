from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class RequestMetric:
    """Telemetry record for a single RELAY request."""

    provider: str
    model: str

    success: bool

    latency_ms: float | None = None

    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None

    attempts: int = 1
    fallback_used: bool = False

    error_type: str | None = None
    error_message: str | None = None

    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    metadata: dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """
    In-memory telemetry collector for RELAY.

    The initial implementation keeps metrics in memory.
    Persistent storage can be added later without changing
    the request-routing architecture.
    """

    def __init__(self) -> None:
        self._metrics: list[RequestMetric] = []

    def record(self, metric: RequestMetric) -> None:
        """Record a telemetry event."""

        self._metrics.append(metric)

    def record_success(
        self,
        *,
        provider: str,
        model: str,
        latency_ms: float | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        total_tokens: int | None = None,
        attempts: int = 1,
        fallback_used: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> RequestMetric:
        """Record a successful request."""

        metric = RequestMetric(
            provider=provider,
            model=model,
            success=True,
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            attempts=attempts,
            fallback_used=fallback_used,
            metadata=metadata or {},
        )

        self.record(metric)

        return metric

    def record_failure(
        self,
        *,
        provider: str,
        model: str,
        error: Exception,
        attempts: int = 1,
        fallback_used: bool = False,
        latency_ms: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RequestMetric:
        """Record a failed request."""

        metric = RequestMetric(
            provider=provider,
            model=model,
            success=False,
            latency_ms=latency_ms,
            attempts=attempts,
            fallback_used=fallback_used,
            error_type=type(error).__name__,
            error_message=str(error),
            metadata=metadata or {},
        )

        self.record(metric)

        return metric

    def all(self) -> list[RequestMetric]:
        """Return a copy of all collected metrics."""

        return list(self._metrics)

    def clear(self) -> None:
        """Remove all collected metrics."""

        self._metrics.clear()

    def count(self) -> int:
        """Return the number of recorded metrics."""

        return len(self._metrics)

    def successful_requests(self) -> list[RequestMetric]:
        """Return successful request metrics."""

        return [
            metric
            for metric in self._metrics
            if metric.success
        ]

    def failed_requests(self) -> list[RequestMetric]:
        """Return failed request metrics."""

        return [
            metric
            for metric in self._metrics
            if not metric.success
        ]

    def provider_stats(self) -> dict[str, dict[str, int]]:
        """
        Return basic success/failure statistics grouped by provider.
        """

        stats: dict[str, dict[str, int]] = {}

        for metric in self._metrics:
            provider = metric.provider

            if provider not in stats:
                stats[provider] = {
                    "requests": 0,
                    "successes": 0,
                    "failures": 0,
                    "fallbacks": 0,
                }

            stats[provider]["requests"] += 1

            if metric.success:
                stats[provider]["successes"] += 1
            else:
                stats[provider]["failures"] += 1

            if metric.fallback_used:
                stats[provider]["fallbacks"] += 1

        return stats

    def summary(self) -> dict[str, Any]:
        """Return an overall telemetry summary."""

        total = len(self._metrics)
        successes = len(self.successful_requests())
        failures = len(self.failed_requests())

        latencies = [
            metric.latency_ms
            for metric in self._metrics
            if metric.latency_ms is not None
        ]

        average_latency = (
            sum(latencies) / len(latencies)
            if latencies
            else None
        )

        total_tokens = sum(
            metric.total_tokens or 0
            for metric in self._metrics
        )

        fallbacks = sum(
            1
            for metric in self._metrics
            if metric.fallback_used
        )

        return {
            "total_requests": total,
            "successful_requests": successes,
            "failed_requests": failures,
            "success_rate": (
                successes / total
                if total
                else None
            ),
            "average_latency_ms": average_latency,
            "total_tokens": total_tokens,
            "fallback_requests": fallbacks,
        }