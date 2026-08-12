from __future__ import annotations

from providers.base import BaseProvider, ModelResponse


class ForcedFailureProvider(BaseProvider):
    """Provider used to simulate a controlled provider outage."""

    def __init__(
        self,
        name: str,
        model: str = "test-model",
        message: str = "simulated provider failure",
    ) -> None:
        super().__init__(
            api_key="test-key",
            model=model,
        )

        self.name = name
        self.message = message

    async def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> ModelResponse:
        raise TimeoutError(self.message)

    async def health_check(self) -> bool:
        return False