from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ModelResponse:
    """Standardized response returned by every RELAY provider."""

    text: str
    provider: str
    model: str

    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None

    finish_reason: str | None = None

    latency_ms: float | None = None

    raw_response: Any = field(default=None, repr=False)


@dataclass
class ProviderError:
    """Standardized description of a provider failure."""

    provider: str
    error_type: str
    message: str

    status_code: int | None = None
    retryable: bool = False

    raw_error: Any = field(default=None, repr=False)


class BaseProvider(ABC):
    """
    Base interface for all AI providers supported by RELAY.

    Provider implementations must translate their native API responses
    into RELAY's standardized ModelResponse format.
    """

    name: str = "unknown"

    def __init__(
        self,
        api_key: str,
        model: str,
        timeout: float = 30.0,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> ModelResponse:
        """
        Generate a response from the provider.

        Implementations must return a standardized ModelResponse.
        """

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check whether the provider is currently available.
        """

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"provider={self.name!r}, "
            f"model={self.model!r}"
            f")"
        )