from __future__ import annotations

from typing import Any

from config.settings import Settings, get_settings
from router.engine import RelayEngine
from schemas.requests import GenerateRequest, GenerateResult
from telemetry.metrics import MetricsCollector


class Relay:
    """
    Public interface for the RELAY model router.
    """

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        engine: RelayEngine | None = None,
        metrics: MetricsCollector | None = None,
    ) -> None:
        self.settings = settings or get_settings()

        # Use one telemetry collector for the entire RELAY instance.
        if metrics is not None:
            self.metrics = metrics
        elif engine is not None:
            self.metrics = engine.metrics
        else:
            self.metrics = MetricsCollector()

        self.engine = engine or RelayEngine(
            settings=self.settings,
            metrics=self.metrics,
        )

    async def generate(
        self,
        prompt: str,
        *,
        model: str | None = None,
        provider: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        metadata: dict[str, Any] | None = None,
        provider_options: dict[str, dict[str, Any]] | None = None,
    ) -> GenerateResult:
        """
        Generate a response through RELAY.

        Routing, failover, and telemetry are handled by the engine.
        """

        request = GenerateRequest(
            prompt=prompt,
            model=model,
            provider=provider,
            temperature=temperature,
            max_tokens=max_tokens,
            metadata=metadata or {},
            provider_options=provider_options or {},
        )

        return await self.engine.generate(request)

    def available_providers(self) -> list[str]:
        """Return providers currently configured for RELAY."""

        return self.engine.available_providers()

    def metrics_summary(self) -> dict[str, Any]:
        """Return the current RELAY telemetry summary."""

        return self.metrics.summary()

    def provider_stats(self) -> dict[str, dict[str, int]]:
        """Return telemetry grouped by provider."""

        return self.metrics.provider_stats()


__all__ = [
    "Relay",
]