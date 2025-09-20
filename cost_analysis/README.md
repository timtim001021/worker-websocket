# Cost Analysis & Optimizations

This folder is for costing, billing models, and optimization experiments.

Key metrics to track
- ASR cost per minute
- LLM tokens per call
- TTS cost per minute
- Recording storage per customer

Short-term recommendations
- Use cloud ASR/LLM for PoC and measure per-minute/token spend.
- Cache repeated TTS outputs and reuse voices for standard prompts.
- Consider 8k telephony audio to save ASR cost (upscale only when necessary).

Files to add
- `models/cost_model.xlsx` or `cost_model.csv` (per-minute estimates)
- `benchmarks/` (run logs with tokens/minute and latency)

Billing model ideas
- Flat per-minute base + per-token surcharge
- Tiered plans (basic/standard/premium) with voice quality differences

Notes
- I can scaffold a simple `cost_model.csv` if you provide provider pricing or let me fetch typical prices.