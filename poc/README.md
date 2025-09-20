# PoC — Practical tasks and artifacts

This folder contains artifacts for the Proof-of-Concept and quick experiments.

Contents and checklist
- `test/` — test clients and audio scripts (already present in this repo).
- `worker/` — edge/worker proof-of-concept (Cloudflare Worker websocket PoC).
- Tasks:
  - [ ] Harden worker input encoding (base64/typed-array) and add diagnostics.
  - [ ] Add CI job to publish worker on commit (`wrangler publish`).
  - [ ] Add automated end-to-end test that streams short audio and verifies transcript.

How to run local tests
- Use `test/stream_audio.py` to stream locally-resampled WAV files to the deployed worker.
- Use `test/record_encoded.py` to capture WAV payload diagnostics for study.

Notes
- Keep PoC code self-contained here. When a PoC feature stabilizes, promote it to `src/` or a production service folder.