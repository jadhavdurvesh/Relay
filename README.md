<div align="center">

<img src="assets/banner.png" alt="RELAY Banner">

# RELAY

### Universal AI Model Router

**One interface. Multiple models. Automatic failover.**

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Status-Under%20Development-orange)]()
[![License](https://img.shields.io/badge/License-DMJ%20Community%20License-blue)](LICENSE)

</div>

---

## What is RELAY?

**RELAY** is a provider-agnostic AI model routing layer that gives applications a unified interface for working with multiple AI model providers.

Instead of integrating every provider separately, an application communicates with RELAY, and RELAY handles provider selection, failover, and future routing intelligence.

```text
                    APPLICATION
                         │
                         ▼
                   ┌───────────┐
                   │   RELAY   │
                   └─────┬─────┘
                         │
            ┌────────────┼────────────┐
            ▼            ▼            ▼
          GROQ         GEMINI     OPENROUTER
```

The goal is simple:

> **Connect once. Route anywhere.**

---

## Why RELAY?

AI applications increasingly depend on multiple model providers.

A provider can become unavailable, rate-limited, slow, expensive, or unsuitable for a particular request.

RELAY provides a layer between the application and those providers so the application does not need to contain provider-specific routing and failover logic.

```text
Application
     │
     ▼
   RELAY
     │
     ▼
Primary Provider
     │
     ├── Success ───────────► Response
     │
     └── Failure
            │
            ▼
      Fallback Provider
            │
            ├── Success ───► Response
            │
            └── Failure
                   │
                   ▼
              Next Provider
```

---

## Core Features

### Multi-Provider Support

RELAY is designed to work with multiple AI providers through a common interface.

Initial providers:

- Groq
- Gemini
- OpenRouter

More providers can be added without changing the core routing architecture.

### Automatic Failover

When a provider fails, RELAY can automatically attempt another configured provider.

```text
Groq
 │
 └── FAILED
       │
       ▼
Gemini
 │
 └── FAILED
       │
       ▼
OpenRouter
 │
 └── SUCCESS
```

### Provider Abstraction

Provider-specific API implementations stay inside their own adapters.

The routing engine interacts with a common provider interface rather than directly with individual APIs.

### Routing

RELAY will support routing decisions based on factors such as:

- Provider priority
- Model capability
- Task type
- Availability
- Latency
- Cost
- Historical performance

### Telemetry

RELAY will track information such as:

- Provider
- Model
- Request status
- Latency
- Token usage
- Retry attempts
- Failover attempts
- Estimated cost

### Benchmarking

RELAY will eventually compare models and providers using the same workload and collect measurable performance data.

### Intelligent Routing

Future versions will use collected benchmark and telemetry data to make increasingly intelligent routing decisions.

---

## Initial Provider Chain

The initial development configuration is:

```text
Priority 1 → Groq
Priority 2 → Gemini
Priority 3 → OpenRouter
```

This is the initial default strategy, not a permanent restriction.

The routing system will eventually allow users to define their own provider order and policies.

---

## Failover Behavior

RELAY should classify failures instead of blindly retrying every error.

Examples of failures that may trigger failover:

```text
429 Too Many Requests
500 Internal Server Error
502 Bad Gateway
503 Service Unavailable
Timeout
Connection Failure
Provider Unavailable
```

Failures that may require configuration or request correction instead of automatic failover include:

```text
Invalid API Key
Authentication Failure
Malformed Request
Unsupported Parameters
Invalid Model
```

The exact behavior will be implemented through the failover policy.

---

## Architecture

```text
                         ┌────────────────────┐
                         │    APPLICATION     │
                         └──────────┬─────────┘
                                    │
                                    ▼
                         ┌────────────────────┐
                         │       RELAY        │
                         │   Model Router     │
                         └──────────┬─────────┘
                                    │
                         ┌──────────▼─────────┐
                         │   Routing Engine   │
                         └──────────┬─────────┘
                                    │
                         ┌──────────▼─────────┐
                         │  Provider Manager  │
                         └──────────┬─────────┘
                                    │
                ┌───────────────────┼───────────────────┐
                ▼                   ▼                   ▼
           ┌─────────┐         ┌─────────┐        ┌────────────┐
           │  Groq   │         │ Gemini  │        │ OpenRouter │
           └────┬────┘         └────┬────┘        └─────┬──────┘
                │                   │                   │
                └───────────────────┼───────────────────┘
                                    │
                                    ▼
                         ┌────────────────────┐
                         │  Failover Engine  │
                         └──────────┬─────────┘
                                    │
                                    ▼
                         ┌────────────────────┐
                         │     Telemetry      │
                         └────────────────────┘
```

---

## Request Flow

A typical request will eventually follow this process:

```text
Request
  │
  ▼
RELAY
  │
  ▼
Classify / Inspect Request
  │
  ▼
Select Provider + Model
  │
  ▼
Send Request
  │
  ├──────── Success ────────► Return Response
  │
  └──────── Failure
             │
             ▼
        Classify Error
             │
             ▼
        Apply Failover Policy
             │
             ▼
        Select Next Provider
             │
             ▼
        Retry Request
             │
             └──────────────► Return Response
```

---

## Telemetry

A request may produce telemetry similar to:

```text
Request ID       : 1842

Primary Provider : Groq
Model            : <model>
Status           : FAILED
Error            : Rate Limited
Latency          : 421 ms

Fallback Provider: Gemini
Model            : <model>
Status           : SUCCESS
Latency          : 803 ms

Final Provider   : Gemini
Fallback Used    : Yes
Attempts         : 2
```

This information will later support:

- Performance analysis
- Provider health tracking
- Cost analysis
- Benchmarking
- Routing optimization

---

## Benchmarking

RELAY will eventually be able to run the same workload against multiple providers.

Example:

```text
                    GROQ      GEMINI      OPENROUTER
-----------------------------------------------------
Latency             0.8 s       1.2 s          1.0 s
Input Tokens         120         120            120
Output Tokens        512         498            534
Estimated Cost       $X          $Y             $Z
Quality Score        89%         93%            91%
```

The benchmark system will make provider and model selection measurable.

---

## Intelligent Routing

The long-term goal is to move beyond static provider priorities.

A future routing engine may consider:

```text
Task Type
Model Capability
Provider Availability
Historical Latency
Historical Quality
Token Usage
Estimated Cost
Current Rate Limits
Previous Failures
```

Conceptually:

```text
                    Incoming Request
                           │
                           ▼
                    Request Analysis
                           │
                           ▼
                   Candidate Models
                           │
                           ▼
                    Routing Engine
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
          Quality         Cost        Latency
             │             │             │
             └─────────────┼─────────────┘
                           ▼
                    Selected Model
```

---

## Project Structure

```text
.
├── assets/
│   └── banner.png
│
├── providers/
│   ├── __init__.py
│   ├── base.py
│   ├── groq.py
│   ├── gemini.py
│   └── openrouter.py
│
├── router/
│   ├── __init__.py
│   ├── engine.py
│   ├── policy.py
│   └── failover.py
│
├── telemetry/
│   ├── __init__.py
│   └── metrics.py
│
├── schemas/
│   ├── __init__.py
│   └── requests.py
│
├── config/
│   ├── __init__.py
│   └── settings.py
│
├── tests/
├── examples/
├── scripts/
│
├── main.py
├── pyproject.toml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Configuration

Provider API keys will be supplied through environment variables.

```env
GROQ_API_KEY=
GEMINI_API_KEY=
OPENROUTER_API_KEY=
```

API keys must never be committed to the repository.

Local development should use environment variables or a local `.env` file.

---

## Example Future Usage

A future RELAY client may look like:

```python
from relay import Relay

client = Relay()

response = client.generate(
    "Explain how PID control works."
)

print(response.text)
```

The application does not need to know which provider ultimately handled the request.

---

## Development Roadmap

### v0.1 — Foundation

- [ ] Repository foundation
- [ ] Provider abstraction
- [ ] Groq integration
- [ ] Gemini integration
- [ ] OpenRouter integration
- [ ] Unified request interface
- [ ] Basic provider selection
- [ ] Automatic failover

### v0.2 — Reliability

- [ ] Error classification
- [ ] Retry policies
- [ ] Provider priorities
- [ ] Timeout handling
- [ ] Rate-limit handling
- [ ] Fallback tracking
- [ ] Provider health state

### v0.3 — Telemetry

- [ ] Request logging
- [ ] Latency tracking
- [ ] Token tracking
- [ ] Cost estimation
- [ ] Provider statistics
- [ ] Failover statistics

### v0.4 — Benchmarking

- [ ] Multi-provider benchmark runner
- [ ] Response comparison
- [ ] Quality evaluation
- [ ] Benchmark reports
- [ ] Historical performance tracking

### v0.5 — Intelligent Routing

- [ ] Task classification
- [ ] Capability-based routing
- [ ] Cost-aware routing
- [ ] Latency-aware routing
- [ ] Quality-aware routing
- [ ] Adaptive routing

### Future

- [ ] Web dashboard
- [ ] REST API
- [ ] Python SDK
- [ ] Streaming support
- [ ] Load balancing
- [ ] Provider health monitoring
- [ ] Model recommendations
- [ ] Advanced routing policies
- [ ] Local model support
- [ ] Custom provider support

---

## Design Principles

### Provider Agnostic

RELAY should not be tied to a single AI provider.

### Resilient

A temporary provider failure should not unnecessarily break the application.

### Observable

Routing decisions and provider performance should be measurable.

### Extensible

Adding a new provider should require minimal changes to the core system.

### Modular

Providers, routing, failover, telemetry, and benchmarking should remain independently maintainable.

### Practical

RELAY is intended to solve real engineering problems rather than simply wrap a single model API.

---

## Project Status

**RELAY is currently under active development.**

The first development goal is a stable multi-provider foundation with:

```text
Groq
Gemini
OpenRouter
     │
     ▼
   RELAY
     │
     ▼
Automatic Failover
```

Intelligent routing and benchmarking will be built on top of this foundation.

---

## License

RELAY is released under the **DMJ Community License (DCL)**.

See [`LICENSE`](LICENSE) for the complete license terms.

---

<div align="center">

**RELAY**

*Connect models. Route intelligently. Stay resilient.*

</div>