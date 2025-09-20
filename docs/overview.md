# Overview — Conversational Phone-line SaaS (Top-level)

Goals
- Real-time conversational agents over PSTN/VoIP.
- Low latency (<1.5–2.5s roundtrip for short replies).
- Cost-efficient and secure (consent, encryption, retention).

Core concepts
- Streaming everywhere: ASR (streaming) -> LLM (streaming) -> TTS (streaming).
- Hybrid routing: small local models for intent + cloud models for heavy generation.
- Early-turn heuristics: use partial transcripts to pre-warm LLM or select templates.

High-level architecture
- Telephony Gateway (Twilio / SignalWire / SIP)
- Media Bridge / WebRTC
- ASR (cloud streaming or local whisper)
- Dialog Manager / LLM (streaming)
- TTS (streaming)
- Storage & Analytics (Postgres, Redis, S3)

Design principles
- Keep per-call paths stateless and store session state in Redis.
- Measure per-call metrics and apply cost/latency budgets.
- Fail gracefully: retries, small local fallbacks, and user-facing clarifications.

Quick links (drill into topics)
- PoC tasks and scripts: `../poc/README.md`
- Implementation roadmap: `../roadmap/README.md`
- Cost analysis & optimizations: `../cost_analysis/README.md`
- Full original plan: `../CONVERSATIONAL_PHONE_SAAS_PLAN.md`

Use this overview as the "zoomed-out" landing page. For detailed decisions and tests, open the relevant subfolder.