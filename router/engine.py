from __future__ import annotations

from typing import Any

from config.settings import Settings, get_settings
from providers.base import BaseProvider, ModelResponse
from providers.gemini import GeminiProvider
from providers.groq import GroqProvider
from providers.openrouter import OpenRouterProvider
from router.failover import FailoverManager
from router.policy import RoutingPolicy
from schemas.requests import GenerateRequest, GenerateResult
from telemetry.metrics import MetricsCollector


class RelayEngine:
    """
    Core RELAY routing engine.

    Responsible for:
    - discovering configured providers
    - selecting providers according to routing policy
    - executing requests
    - handling provider failures
    - performing automatic failover
    - recording provider telemetry
    - returning standardized results
    """

    DEFAULT_MODELS = {
        "groq": "llama-3.3-70b-versatile",
        "gemini": "gemini-2.5-flash",
        "openrouter": "openai/gpt-4o-mini",
    }

    def __init__(
        self,
        settings: Settings | None = None,
        providers: dict[str, BaseProvider] | None = None,
        policy: RoutingPolicy | None = None,
        failover: FailoverManager | None = None,
        metrics: MetricsCollector | None = None,
    ) -> None:
        self.settings = settings or get_settings()

        self.providers = (
            providers
            if providers is not None
            else self._build_providers()
        )

        self.policy = policy or RoutingPolicy(
            provider_order=tuple(self.settings.providers),
            max_attempts=self.settings.max_attempts,
            enable_failover=self.settings.enable_failover,
        )

        self.failover = failover or FailoverManager()
        self.metrics = metrics or MetricsCollector()

    def _build_providers(self) -> dict[str, BaseProvider]:
        """Build provider adapters from configured API keys."""

        providers: dict[str, BaseProvider] = {}

        if self.settings.groq_api_key:
            providers["groq"] = GroqProvider(
                api_key=self.settings.groq_api_key,
                model=self.DEFAULT_MODELS["groq"],
                timeout=self.settings.timeout,
            )

        if self.settings.gemini_api_key:
            providers["gemini"] = GeminiProvider(
                api_key=self.settings.gemini_api_key,
                model=self.DEFAULT_MODELS["gemini"],
                timeout=self.settings.timeout,
            )

        if self.settings.openrouter_api_key:
            providers["openrouter"] = OpenRouterProvider(
                api_key=self.settings.openrouter_api_key,
                model=self.DEFAULT_MODELS["openrouter"],
                timeout=self.settings.timeout,
            )

        return providers

    def available_providers(self) -> list[str]:
        """Return configured providers that are available to RELAY."""

        return [
            provider
            for provider in self.policy.provider_order
            if provider in self.providers
        ]

    def _get_provider(
        self,
        provider_name: str,
    ) -> BaseProvider:
        """Return a configured provider."""

        provider = self.providers.get(provider_name)

        if provider is None:
            raise ValueError(
                f"Provider '{provider_name}' is not configured or unavailable."
            )

        return provider

    def _provider_options(
        self,
        request: GenerateRequest,
        provider_name: str,
    ) -> dict[str, Any]:
        """Return provider-specific options."""

        return dict(
            request.provider_options.get(
                provider_name,
                {},
            )
        )

    async def generate(
        self,
        request: GenerateRequest,
    ) -> GenerateResult:
        """Execute a generation request through RELAY."""

        available = self.available_providers()

        if not available:
            raise RuntimeError(
                "No AI providers are configured. "
                "Add at least one provider API key to the environment."
            )

        # ------------------------------------------
        # Provider selection
        # ------------------------------------------

        if request.provider:
            requested_provider = request.provider.lower().strip()

            if requested_provider not in self.providers:
                raise ValueError(
                    f"Requested provider '{requested_provider}' "
                    "is not configured."
                )

            provider_names = [requested_provider]

            if self.settings.enable_failover:
                remaining = [
                    provider
                    for provider in available
                    if provider != requested_provider
                ]

                provider_names.extend(
                    remaining[: self.settings.max_attempts - 1]
                )
        else:
            provider_names = self.policy.select_providers(
                available
            )

        if not provider_names:
            raise RuntimeError(
                "No suitable providers are available for this request."
            )

        # ------------------------------------------
        # Request execution
        # ------------------------------------------

        attempts = 0
        last_error: Exception | None = None

        for provider_name in provider_names:
            provider = self._get_provider(provider_name)

            attempts += 1

            model = request.model or provider.model

            options = self._provider_options(
                request,
                provider_name,
            )

            try:
                response: ModelResponse = await provider.generate(
                    request.prompt,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    **options,
                )

                fallback_used = attempts > 1

                self.metrics.record_success(
                    provider=provider_name,
                    model=model,
                    latency_ms=response.latency_ms,
                    input_tokens=response.input_tokens,
                    output_tokens=response.output_tokens,
                    total_tokens=response.total_tokens,
                    attempts=attempts,
                    fallback_used=fallback_used,
                    metadata=request.metadata,
                )

                return GenerateResult(
                    text=response.text,
                    provider=response.provider,
                    model=model,
                    latency_ms=response.latency_ms,
                    input_tokens=response.input_tokens,
                    output_tokens=response.output_tokens,
                    total_tokens=response.total_tokens,
                    attempts=attempts,
                    fallback_used=fallback_used,
                    metadata={
                        **request.metadata,
                    },
                )

            except Exception as error:
                last_error = error

                decision = self.failover.classify(error)

                self.metrics.record_failure(
                    provider=provider_name,
                    model=model,
                    error=error,
                    attempts=attempts,
                    fallback_used=attempts > 1,
                    metadata={
                        **request.metadata,
                        "failover_reason": decision.reason,
                    },
                )

                if not decision.retryable:
                    raise

                if not self.settings.enable_failover:
                    raise

                continue

        if last_error is not None:
            raise RuntimeError(
                f"All RELAY providers failed after {attempts} attempt(s)."
            ) from last_error

        raise RuntimeError(
            "RELAY failed without receiving a provider response."
        )