from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class RoutingPolicy:
    """
    Defines how RELAY selects providers.

    Providers are evaluated in the order supplied by `provider_order`.
    """

    provider_order: tuple[str, ...] = (
        "groq",
        "gemini",
        "openrouter",
    )

    max_attempts: int = 3
    enable_failover: bool = True

    def __post_init__(self) -> None:
        normalized = tuple(
            provider.strip().lower()
            for provider in self.provider_order
            if provider.strip()
        )

        if not normalized:
            raise ValueError("Routing policy must contain at least one provider.")

        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1.")

        object.__setattr__(self, "provider_order", normalized)

    def select_providers(
        self,
        available_providers: Iterable[str],
    ) -> list[str]:
        """
        Return available providers in routing priority order.
        """

        available = {
            provider.strip().lower()
            for provider in available_providers
        }

        selected = [
            provider
            for provider in self.provider_order
            if provider in available
        ]

        if not self.enable_failover:
            return selected[:1]

        return selected[: self.max_attempts]

    def next_provider(
        self,
        current_provider: str,
        available_providers: Iterable[str],
    ) -> str | None:
        """
        Return the next provider after the current provider.

        Returns None when there is no suitable fallback.
        """

        providers = self.select_providers(available_providers)

        current = current_provider.strip().lower()

        try:
            current_index = providers.index(current)
        except ValueError:
            return providers[0] if providers else None

        next_index = current_index + 1

        if next_index >= len(providers):
            return None

        return providers[next_index]