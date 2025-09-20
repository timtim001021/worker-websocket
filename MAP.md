Project Map — Conversational Phone-line SaaS (plain-text)

Top-level (zoomed out)

- CONVERSATIONAL_PHONE_SAAS_PLAN.md    # Full plan (master document)
- MAP.md                               # This plain-text map (you are here)
- README.md                            # Short repo landing (summary)
- docs/                                # Concise docs and mindmap
  - overview.md                        # Top-level overview
  - mindmap.md                          # Mermaid visual map (optional)
- poc/                                 # Proof-of-concept artifacts
  - README.md                          # PoC checklist and notes
  - worker/                             # Worker/edge code and experiments (src/worker.js)
  - test/                               # test scripts: stream_audio.py, record_encoded.py, encoded_records/
- cost_analysis/                       # Cost models & optimization notes
- roadmap/                             # Roadmap and milestone checklists

How to use this map (zoom & focus)

- Zoom out: read `CONVERSATIONAL_PHONE_SAAS_PLAN.md` and `docs/overview.md` for goals and architecture.
- Zoom in: open a folder listed above (poc/, roadmap/, cost_analysis/) to see concrete tasks, scripts, and notes.
- Focus on a task: each `workflows/` doc below maps to repeatable steps you can run.

Workflows (quick links)
- workflows/deploy.md        # How to publish the Cloudflare Worker
- workflows/streaming-test.md # How to run streaming tests (5s/10s/full) and capture results
- workflows/debug-3010.md    # Debugging intermittent 3010 errors and what to log

Notes
- Keep high-level design on the top level; move experimental code and long analyses into subfolders so the top-level stays browsable.
- Use `workflows/` to store repeatable step-by-step commands so an agent (or you) can run tasks reliably.

Status (current)
- PoC worker (WebSocket) lives at `src/worker.js`.
- Test scripts under `poc/test/` and `test/` — streaming client and recorder exist.
- Diagnostics: `test/encoded_records/` stores recorded payloads for offline analysis.

Next suggestions
- Wire simple README links to the `workflows/` files.
- Keep this MAP.md updated as tasks complete or new workflows are added.




