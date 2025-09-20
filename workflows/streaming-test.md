Workflow: Streaming Tests (how to run and capture results)

Purpose: Run the streaming client to send WAV files to the deployed Worker and capture responses and diagnostics.

Prerequisites
- Python 3 with `websockets` package installed (pip install websockets)
- Test WAV files (5s/10s/full) resampled to 16k mono 16-bit
- Worker deployed and reachable at `wss://<your-worker>.workers.dev`

Commands (from `test/` directory)

1. Stream 5s file

```bash
python3 ./stream_audio.py --file /tmp/enrollment_katie_5s_16k.wav
```

2. Stream 10s file

```bash
python3 ./stream_audio.py --file /tmp/enrollment_katie_10s_16k.wav
```

3. Stream full file

```bash
python3 ./stream_audio.py --file /tmp/enrollment_katie.wav
```

Capture diagnostics
- Use `test/record_encoded.py` to write `encoded_records/` that include head/tail base64 and metadata for each WAV you test:

```bash
python3 ./record_encoded.py --file /tmp/enrollment_katie_10s_16k.wav
```

- Inspect recorded responses and worker logs. If you enabled observability in `wrangler.toml`, review Cloudflare logs for failing requests.

What to look for
- Repeated `chunk_received` acks during streaming.
- `transcription` payload after `end_stream` or `error` payload with `AiError` and stack for failures.
- For failures, record `head.b64` and `tail.b64` and paste them into a ticket.

Notes
- Use shorter clips if Cloudflare kills the worker due to CPU time on long inputs.
- The client warns if sample rate != 16000.

