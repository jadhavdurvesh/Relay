from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class GenerateRequest(BaseModel):
    """Standard request entering the RELAY routing engine."""

    model_config = ConfigDict(extra="allow")

    prompt: str = Field(
        min_length=1,
        description="User prompt sent to the selected model.",
    )

    model: str | None = Field(
        default=None,
        description="Optional model override.",
    )

    provider: str | None = Field(
        default=None,
        description="Optional provider override.",
    )

    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
    )

    max_tokens: int | None = Field(
        default=None,
        gt=0,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional metadata associated with the request.",
    )

    provider_options: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Provider-specific optional parameters.",
    )


class GenerateResult(BaseModel):
    """Standard result returned by the RELAY routing engine."""

    text: str

    provider: str
    model: str

    latency_ms: float | None = None

    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None

    attempts: int = 1
    fallback_used: bool = False

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )