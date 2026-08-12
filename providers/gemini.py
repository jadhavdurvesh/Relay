from __future__ import annotations

import time
from typing import Any

import httpx

from providers.base import BaseProvider, ModelResponse


class GeminiProvider(BaseProvider):
    """Google Gemini provider adapter for RELAY."""

    name = "gemini"

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.5-flash",
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
        """Generate a response using Gemini."""

        url = f"{self.BASE_URL}/{self.model}:generateContent"

        generation_config: dict[str, Any] = {
            "temperature": temperature,
        }

        if max_tokens is not None:
            generation_config["maxOutputTokens"] = max_tokens

        generation_config.update(kwargs.pop("generation_config", {}))

        payload: dict[str, Any] = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt,
                        }
                    ]
                }
            ],
            "generationConfig": generation_config,
        }

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }

        start_time = time.perf_counter()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url,
                headers=headers,
                json=payload,
            )

        latency_ms = (time.perf_counter() - start_time) * 1000

        response.raise_for_status()

        data = response.json()

        candidates = data.get("candidates", [])

        if not candidates:
            raise RuntimeError("Gemini returned no candidates.")

        candidate = candidates[0]

        parts = candidate.get("content", {}).get("parts", [])

        text = "".join(
            part.get("text", "")
            for part in parts
            if isinstance(part, dict)
        )

        usage = data.get("usageMetadata", {})

        return ModelResponse(
            text=text,
            provider=self.name,
            model=self.model,
            input_tokens=usage.get("promptTokenCount"),
            output_tokens=usage.get("candidatesTokenCount"),
            total_tokens=usage.get("totalTokenCount"),
            finish_reason=candidate.get("finishReason"),
            latency_ms=latency_ms,
            raw_response=data,
        )

    async def health_check(self) -> bool:
        """Check whether the Gemini provider is reachable."""

        url = f"{self.BASE_URL}?key={self.api_key}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)

            return response.is_success

        except httpx.HTTPError:
            return False