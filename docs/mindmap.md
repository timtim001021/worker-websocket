# Mindmap — Conversational Phone-line SaaS

This is a navigable, zoomable outline. Use a Markdown viewer that supports Mermaid to render the diagram.

```mermaid
flowchart TB
  A[Overview]
  A --> B(Telephony)
  A --> C(ASR)
  A --> D(LLM/Dialog)
  A --> E(TTS)
  A --> F(Orchestration)
  A --> G(Storage & Analytics)
  B --> B1(Twilio)
  B --> B2(SignalWire)
  B --> B3(Self-hosted SIP)
  C --> C1(Cloud streaming ASR)
  C --> C2(Self-hosted Whisper)
  D --> D1(Hosted LLMs)
  D --> D2(Self-hosted LLMs)
  E --> E1(Cloud TTS)
  E --> E2(Self-hosted TTS)
  F --> F1(Media bridge)
  F --> F2(Dialog manager)
  F --> F3(Hybrid routing)

  click B1 "../docs/telephony_twilio.md" "Twilio notes"
  click C1 "../docs/asr_cloud.md" "Cloud ASR notes"
  click D1 "../docs/llm_hosted.md" "Hosted LLM notes"

  classDef core fill:#f9f,stroke:#333,stroke-width:1px;
  class A core
```

Notes
- The `click` links assume you place detailed docs in `docs/`; I can add these files if you want.
- Mermaid is a convenient way to "zoom" by opening the linked files from nodes.