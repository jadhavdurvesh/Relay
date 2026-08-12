from __future__ import annotations

import asyncio

from main import Relay
from router.engine import RelayEngine
from tests.helpers import ForcedFailureProvider


async def main() -> None:
    relay = Relay()

    real_gemini = relay.engine.providers.get("gemini")

    if real_gemini is None:
        print("Gemini is not configured.")
        return

    providers = dict(relay.engine.providers)

    providers["groq"] = ForcedFailureProvider(
        "groq",
        model="simulated-groq",
    )

    relay.engine = RelayEngine(
        settings=relay.settings,
        providers=providers,
        metrics=relay.metrics,
    )

    result = await relay.generate(
        "Reply with exactly: RELAY failover successful.",
    )

    print("Provider :", result.provider)
    print("Model    :", result.model)
    print("Attempts :", result.attempts)
    print("Fallback :", result.fallback_used)
    print("Latency  :", result.latency_ms, "ms")
    print("Response :", result.text)

    print()
    print("Telemetry:")
    print(relay.metrics_summary())


if __name__ == "__main__":
    asyncio.run(main())