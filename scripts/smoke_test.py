from __future__ import annotations

import asyncio

from main import Relay


async def main() -> None:
    relay = Relay()

    providers = relay.available_providers()

    print("RELAY providers:", providers)

    if not providers:
        print()
        print("No providers are configured.")
        print("Add at least one API key to .env.")
        return

    print()
    print("Sending test request...")
    print()

    result = await relay.generate(
        "Reply with exactly: RELAY connection successful.",
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