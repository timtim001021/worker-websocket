# Implementation Roadmap & Milestones

Phase 0 — Research & infra setup (1–2 weeks)
- Choose telephony provider and create test account.
- Prototype streaming from provider -> microservice.

Phase 1 — Minimal Viable PoC (2–4 weeks)
- Inbound call -> ASR -> LLM -> TTS (no persistence beyond logs).

Phase 2 — Beta (4–8 weeks)
- Session persistence, retries, monitoring, customer config, billing hooks.

Phase 3 — Scale & optimization (ongoing)
- Replace/augment hosted ASR/LLM with self-hosted where cost-effective.
- Autoscaling, regional infra, advanced features.

Testing & metrics
- Unit tests for dialog manager
- Integration tests for end-to-end call replay
- Latency smoke tests (95th percentile)

Notes
- Use this folder to track milestone checklists and include links to runbooks and dashboards.