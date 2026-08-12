from __future__ import annotations

import time
from typing import Any

import httpx

from providers.base import BaseProvider, ModelResponse


class OpenRouterProvider(BaseProvider):
    """OpenRouter provider adapter for RELAY."""

    name = "openrouter"

    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(
        self,
        api_key: str,
        model: str = "openai/gpt-4o-mini",
        timeout: float = 30.0,
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model,
            timeout=timeout,
        )

    async def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> ModelResponse:
        """Generate a response using OpenRouter."""

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "temperature": temperature,
        }

        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        payload.update(kwargs)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        start_time = time.perf_counter()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.BASE_URL,
                headers=headers,
                json=payload,
            )

        latency_ms = (time.perf_counter() - start_time) * 1000

        response.raise_for_status()

        data = response.json()

        choices = data.get("choices", [])

        if not choices:
            raise RuntimeError("OpenRouter returned no choices.")

        choice = choices[0]
        message = choice.get("message", {})

        usage = data.get("usage", {})

        return ModelResponse(
            text=message.get("content", ""),
            provider=self.name,
            model=data.get("model", self.model),
            input_tokens=usage.get("prompt_tokens"),
            output_tokens=usage.get("completion_tokens"),
            total_tokens=usage.get("total_tokens"),
            finish_reason=choice.get("finish_reason"),
            latency_ms=latency_ms,
            raw_response=data,
        )

    async def health_check(self) -> bool:
        """Check whether OpenRouter is reachable."""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    "https://openrouter.ai/api/v1/models",
                    headers=headers,
                )

            return response.is_success

        except httpx.HTTPError:
            return False