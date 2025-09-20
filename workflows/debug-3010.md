Workflow: Debug intermittent AiError 3010 (Invalid audio input)

Goal: Capture diagnostics and apply mitigations for intermittent "3010: Invalid or incomplete input for the model" errors from Workers AI.

Immediate hypotheses
- Large JSON numeric arrays ([...wavBytes]) get truncated or mishandled in serialization.
- Worker/AI runtime limits cause partial payloads or aborted processing.
- Header/data mismatch or endianness (less likely given local records)

What to log (minimum)
- Before calling `env.AI.run`, send a small diagnostic message and console.log with:
  - `bytesLength`: wavBytes.length
  - `samples`: number of samples
  - `sampleRate`: value used in header
  - `headBase64`: base64(first 64 bytes)
  - `tailBase64`: base64(last 64 bytes)

Mitigations to implement
1. Switch to base64 data URL for `audio` in `AI.run` calls:
   - `audio: 'data:audio/wav;base64,' + base64(wavBytes)`
2. If 1 fails or isn't supported, try passing the typed array / ArrayBuffer if allowed:
   - `audio: wavBytes` or `audio: wavBytes.buffer`
3. Add a retry-on-3010 with one retry using alternate encoding (base64)

Reproduction steps
1. Deploy worker with diagnostic logging enabled.
2. Stream the full file; if 3010 appears, retrieve worker logs and the diagnostic head/tail base64 strings.
3. Compare head/tail from `test/encoded_records/` with worker diagnostic to see if payload was truncated or header altered.

Next actions
- Implement diagnostic logging and base64 fallback in `src/worker.js`; keep logs minimal to avoid excessive noise.
- Deploy and re-run failing input to collect evidence.

