// Real-world WebSocket Worker for Conversational Phone SaaS
export default {
  async fetch(request, env) {
    // Handle WebSocket upgrade for real-time audio streaming
    if (request.headers.get('Upgrade') === 'websocket') {
      const upgradeHeader = request.headers.get('Upgrade');
      const websocketKey = request.headers.get('Sec-WebSocket-Key');

      if (!upgradeHeader || !websocketKey) {
        return new Response('WebSocket upgrade required', { status: 400 });
      }

      // Create WebSocket pair
      const webSocketPair = new WebSocketPair();
      const client = webSocketPair[0];
      const server = webSocketPair[1];

      // Handle WebSocket connection
      server.accept();

      // Debug flag: enable with ?debug=1 on the WebSocket URL
      const DEBUG_INCOMING = (new URL(request.url).searchParams.get('debug') === '1');

      // Initialize session state
      const session = {
        id: crypto.randomUUID(),
        audioBuffer: [],
        lastActivity: Date.now(),
        isProcessing: false
      };

      console.log(`New WebSocket session: ${session.id}`);

        // Handle incoming messages (non-blocking): do not await long-running work inside the event handler
        // Support both text JSON messages and binary frames (binary frames start with 0x01 then uint16 sample count, then Int16 samples)
        server.addEventListener('message', (event) => {
          // Debug: inspect the incoming message briefly if enabled via ?debug=1
          if (DEBUG_INCOMING) {
            try {
              let info = { typeof: typeof event.data };
              if (typeof event.data === 'string') {
                info.preview = event.data.slice(0, 256);
              } else {
                // try typed-array view
                if (event.data instanceof ArrayBuffer) {
                  const ua = new Uint8Array(event.data);
                  const hex = Array.from(ua.subarray(0, Math.min(16, ua.length))).map(b => b.toString(16).padStart(2,'0')).join(' ');
                  info.previewHex = hex;
                } else if (ArrayBuffer.isView(event.data)) {
                  const ua = new Uint8Array(event.data.buffer, event.data.byteOffset || 0, Math.min(16, event.data.byteLength || event.data.buffer.byteLength));
                  const hex = Array.from(ua).map(b => b.toString(16).padStart(2,'0')).join(' ');
                  info.previewHex = hex;
                }
              }
              console.log('incoming message info:', info);
            } catch (e) { console.warn('incoming debug failed', e?.message); }
          }
          // Update activity timestamp and reset idle timer
          session.lastActivity = Date.now();
          if (session.idleTimer) {
            clearTimeout(session.idleTimer);
          }
          // set new idle timer to close session after 120s of inactivity
          session.idleTimer = setTimeout(() => {
            try { server.send(JSON.stringify({ type: 'session_closed', reason: 'idle_timeout' })); } catch(e){}
            try { server.close(); } catch(e){}
            console.log(`Session ${session.id} closed due to idle timeout`);
          }, 120 * 1000);

          // Robust binary message detection: accept ArrayBuffer, TypedArray views, and DataView
          let raw = event.data;
          let buf = null;
          if (typeof raw !== 'string') {
            // ArrayBuffer
            if (raw instanceof ArrayBuffer) {
              buf = new Uint8Array(raw);
            } else if (ArrayBuffer.isView(raw)) {
              // TypedArray or DataView
              buf = new Uint8Array(raw.buffer, raw.byteOffset || 0, raw.byteLength || raw.buffer.byteLength);
            } else if (raw && raw.buffer instanceof ArrayBuffer) {
              buf = new Uint8Array(raw.buffer);
            }
          }

          if (buf) {
            try {
              if (buf.length >= 3 && buf[0] === 0x01) {
                // audio binary frame
                const dv = new DataView(buf.buffer, buf.byteOffset, buf.byteLength);
                const sampleCount = dv.getUint16(1, true);
                // Int16 samples start at offset 3; ensure we have enough bytes
                const expectedBytes = sampleCount * 2;
                if (buf.byteLength < 3 + expectedBytes) throw new Error('binary frame too short');
                // Create a compact copy of the sample bytes (aligned) to avoid TypedArray byteOffset alignment requirements
                const sampleBytes = buf.subarray(3, 3 + expectedBytes);
                let samples;
                try {
                  // Fast path: copy the bytes and view as Int16Array
                  const sampleCopy = sampleBytes.slice(); // creates a new ArrayBuffer with byteOffset === 0
                  samples = new Int16Array(sampleCopy.buffer);
                } catch (e) {
                  // Fallback: some engines may throw if we try to create typed arrays from unaligned buffers.
                  // Use DataView.getInt16 to build the Int16Array explicitly.
                  const dvSamples = new Int16Array(sampleCount);
                  const sampleDv = new DataView(sampleBytes.buffer, sampleBytes.byteOffset, sampleBytes.byteLength);
                  for (let i = 0; i < sampleCount; i++) {
                    dvSamples[i] = sampleDv.getInt16(i * 2, true);
                  }
                  samples = dvSamples;
                }
                // push samples into session buffer
                for (let i = 0; i < samples.length; i++) session.audioBuffer.push(samples[i]);
                // send ack
                try { server.send(JSON.stringify({ type: 'chunk_received', chunk_size: samples.length, buffer_size: session.audioBuffer.length })); } catch(e){}
                return;
              }
            } catch (err) {
              console.error('Binary message handling error:', err?.message);
              try { server.send(JSON.stringify({ type: 'error', message: 'Invalid binary frame', error: { message: err?.message } })); } catch(e){}
              return;
            }
          }

          // Otherwise, assume text JSON
          let data;
          try {
            data = JSON.parse(event.data);
          } catch (error) {
            console.error('Message parse error:', error?.message);
            server.send(JSON.stringify({ type: 'error', message: 'Invalid message format', error: { message: error?.message } }));
            return;
          }

          try {
            if (data.type === 'audio_chunk') {
              // fire-and-forget: handle chunk asynchronously
              handleAudioChunk(server, data, session, env).catch((err) => {
                console.error('handleAudioChunk error:', err?.message, err?.stack);
                try { server.send(JSON.stringify({ type: 'error', message: 'Chunk handling failed', error: { message: err?.message } })); } catch(e){}
              });
            } else if (data.type === 'end_stream') {
              // process accumulated audio asynchronously
              processAudioBuffer(server, session, env).catch((err) => {
                console.error('processAudioBuffer error:', err?.message, err?.stack);
                try { server.send(JSON.stringify({ type: 'error', message: 'Processing failed', error: { message: err?.message } })); } catch(e){}
              });
            } else if (data.type === 'ping') {
              // Keep-alive
              server.send(JSON.stringify({ type: 'pong', timestamp: Date.now() }));
            } else if (data.type === 'dump_wav' || data.type === 'echo_wav') {
              // Client requests the assembled WAV for debugging/inspection
              try {
                if (!session.audioBuffer || session.audioBuffer.length === 0) {
                  server.send(JSON.stringify({ type: 'error', message: 'No audio buffered' }));
                } else {
                  const int16 = Int16Array.from(session.audioBuffer);
                  const audioBytes = new Uint8Array(int16.buffer);

                  // build minimal WAV (same format as processing)
                  const buildWavBytes = (pcmBytes, sampleRate = 16000, numChannels = 1, bitsPerSample = 16) => {
                    const header = new ArrayBuffer(44);
                    const view = new DataView(header);
                    const blockAlign = numChannels * bitsPerSample / 8;
                    const byteRate = sampleRate * blockAlign;
                    const dataSize = pcmBytes.length;
                    const writeString = (view, offset, str) => { for (let i = 0; i < str.length; i++) view.setUint8(offset + i, str.charCodeAt(i)); };
                    writeString(view, 0, 'RIFF');
                    view.setUint32(4, 36 + dataSize, true);
                    writeString(view, 8, 'WAVE');
                    writeString(view, 12, 'fmt ');
                    view.setUint32(16, 16, true);
                    view.setUint16(20, 1, true);
                    view.setUint16(22, numChannels, true);
                    view.setUint32(24, sampleRate, true);
                    view.setUint32(28, byteRate, true);
                    view.setUint16(32, blockAlign, true);
                    view.setUint16(34, bitsPerSample, true);
                    writeString(view, 36, 'data');
                    view.setUint32(40, dataSize, true);
                    const wav = new Uint8Array(44 + dataSize);
                    wav.set(new Uint8Array(header), 0);
                    wav.set(pcmBytes, 44);
                    return wav;
                  };

                  const wavBytes = buildWavBytes(audioBytes, 16000, 1, 16);
                  // limit size to 2MB in worker response to avoid huge messages
                  if (wavBytes.length > 2 * 1024 * 1024) {
                    server.send(JSON.stringify({ type: 'error', message: 'WAV too large to dump', size: wavBytes.length }));
                  } else {
                    // base64 encode
                    let binary = '';
                    const chunkSize = 0x8000;
                    for (let i = 0; i < wavBytes.length; i += chunkSize) {
                      const slice = wavBytes.subarray(i, i + chunkSize);
                      binary += String.fromCharCode.apply(null, slice);
                    }
                    const b64 = btoa(binary);
                    server.send(JSON.stringify({ type: 'echo_wav', wavBase64: b64, sampleRate: 16000, samples: int16.length }));
                  }
                }
              } catch (err) {
                console.error('dump_wav failed', err?.message);
                try { server.send(JSON.stringify({ type: 'error', message: 'dump_wav failed', error: { message: err?.message } })); } catch(e){}
              }
            }
          } catch (error) {
            console.error('Message handling error:', error?.message, error?.stack);
            try { server.send(JSON.stringify({ type: 'error', message: 'Failed to process message', error: { message: error?.message } })); } catch(e){}
          }
        });

      // Handle connection close
      server.addEventListener('close', () => {
        console.log(`Session ${session.id} closed`);
      });

      // Handle connection errors
      server.addEventListener('error', (error) => {
        console.error(`Session ${session.id} error:`, error);
      });

      return new Response(null, {
        status: 101,
        webSocket: client,
      });
    }

    // Handle HTTP requests (for health checks, etc.)
    if (request.method === 'GET' && new URL(request.url).pathname === '/health') {
      return Response.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        version: '1.0.0'
      });
    }

    return new Response('WebSocket connection required', { status: 426 });
  }
};

  // Hoisted helper: wrap a promise with a timeout to avoid indefinite hangs when calling AI.run
  function withTimeout(p, ms) {
    return Promise.race([
      p,
      new Promise((_, rej) => setTimeout(() => rej(new Error('AI.run timed out')), ms))
    ]);
  }

async function handleAudioChunk(ws, data, session, env) {
  // Add audio chunk to buffer
  session.audioBuffer.push(...data.audio);

  // Send acknowledgment
  ws.send(JSON.stringify({
    type: 'chunk_received',
    chunk_size: data.audio.length,
    buffer_size: session.audioBuffer.length
  }));

  // Do not auto-process here to avoid many AI.run calls and potential format issues.
  // Processing will occur on explicit 'end_stream' from the client.
}

async function processAudioBuffer(ws, session, env) {
  if (session.isProcessing || session.audioBuffer.length === 0) {
    return;
  }

  session.isProcessing = true;

  try {
    // session.audioBuffer contains int16 samples (signed 16-bit)
    // Convert the array of int samples into an Int16Array and get the underlying bytes
    const int16 = Int16Array.from(session.audioBuffer);
    const audioBytes = new Uint8Array(int16.buffer);

    console.log(`Processing ${audioBytes.length} bytes (${int16.length} samples) of audio for session ${session.id}`);

    // Build a minimal WAV header (PCM 16-bit, mono)
    const buildWav = (pcmBytes, sampleRate = 16000, numChannels = 1, bitsPerSample = 16) => {
      const header = new ArrayBuffer(44);
      const view = new DataView(header);
      const blockAlign = numChannels * bitsPerSample / 8;
      const byteRate = sampleRate * blockAlign;
      const dataSize = pcmBytes.length; // bytes

      // RIFF identifier
      writeString(view, 0, 'RIFF');
      view.setUint32(4, 36 + dataSize, true); // file length - 8
      writeString(view, 8, 'WAVE');
      writeString(view, 12, 'fmt ');
      view.setUint32(16, 16, true); // PCM chunk length
      view.setUint16(20, 1, true); // Audio format (1 = PCM)
      view.setUint16(22, numChannels, true);
      view.setUint32(24, sampleRate, true);
      view.setUint32(28, byteRate, true);
      view.setUint16(32, blockAlign, true);
      view.setUint16(34, bitsPerSample, true);
      writeString(view, 36, 'data');
      view.setUint32(40, dataSize, true);

      const wav = new Uint8Array(44 + dataSize);
      wav.set(new Uint8Array(header), 0);
      wav.set(pcmBytes, 44);
      return wav;
    };

    const writeString = (view, offset, str) => {
      for (let i = 0; i < str.length; i++) {
        view.setUint8(offset + i, str.charCodeAt(i));
      }
    };

    const wavBytes = buildWav(audioBytes, 16000, 1, 16);

    // Helper: convert Uint8Array to base64 (chunked to avoid call-size limits)
    const bytesToBase64 = (bytes) => {
      let binary = '';
      const chunkSize = 0x8000; // 32KB chunk
      for (let i = 0; i < bytes.length; i += chunkSize) {
        const slice = bytes.subarray(i, i + chunkSize);
        binary += String.fromCharCode.apply(null, slice);
      }
      return btoa(binary);
    };

    // Send lightweight diagnostics (head/tail + sizes) so we can correlate failures
    try {
      const head = bytesToBase64(wavBytes.subarray(0, Math.min(64, wavBytes.length)));
      const tail = bytesToBase64(wavBytes.subarray(Math.max(0, wavBytes.length - 64)));
      const debugMsg = {
        type: 'processing_debug',
        bytesLength: wavBytes.length,
        samples: int16.length,
        sampleRate: 16000,
        headBase64: head,
        tailBase64: tail,
        timestamp: Date.now()
      };
      // best-effort send; ignore failures
      try { ws.send(JSON.stringify(debugMsg)); } catch(e){}
      console.log('Processing debug:', { bytesLength: wavBytes.length, samples: int16.length });
    } catch (e) {
      console.warn('Failed to generate processing debug', e?.message);
    }

    // Helper: wrap a promise with a timeout to avoid indefinite hangs
    const withTimeout = (p, ms) => Promise.race([
      p,
      new Promise((_, rej) => setTimeout(() => rej(new Error('AI.run timed out')), ms))
    ]);

    // Try several payload shapes to find what the AI binding accepts for audio.
    const base64 = bytesToBase64(wavBytes);
    const dataUrl = 'data:audio/wav;base64,' + base64;

    const payloadAttempts = [
      { desc: 'object-audio-uint8', payload: { audio: wavBytes } },
      { desc: 'object-audio-base64', payload: { audio: base64 } },
      { desc: 'object-audio-dataUrl', payload: { audio: dataUrl } },
      { desc: 'string-dataUrl', payload: dataUrl },
      { desc: 'object-audio-array', payload: { audio: Array.from(wavBytes) } },
      { desc: 'object-input-dataUrl', payload: { input: dataUrl } },
      // Additional plausible shapes
      { desc: 'object-audio-content', payload: { audio: { content: base64 } } },
      { desc: 'object-audio-data', payload: { audio: { data: base64 } } },
      { desc: 'object-file-dataUrl', payload: { file: dataUrl } },
      { desc: 'object-content-dataUrl', payload: { content: dataUrl } },
      { desc: 'object-input-audio', payload: { input: { audio: dataUrl } } },
      { desc: 'object-audio_url', payload: { audio_url: dataUrl } },
      { desc: 'object-url', payload: { url: dataUrl } },
      { desc: 'object-media', payload: { media: dataUrl } }
    ];

    let sttResponse = null;
    for (const attempt of payloadAttempts) {
      try {
        console.log('AI.run attempt:', attempt.desc, typeof attempt.payload, Array.isArray(attempt.payload) ? 'array' : Object.keys(attempt.payload || {}));
        sttResponse = await withTimeout(env.AI.run('@cf/openai/whisper', attempt.payload), 20000);
        console.log('AI.run succeeded with attempt:', attempt.desc);
        break;
      } catch (err) {
        // Log detailed error for this attempt so we can see why schema rejected it
        console.warn('AI.run attempt failed:', attempt.desc, err?.message);
        console.warn(err?.stack || err);
        // keep trying next shapes
      }
    }
    if (!sttResponse) {
      const err = new Error('All AI.run payload attempts failed');
      console.error(err);
      throw err;
    }

  // Log raw STT response for diagnostics and extract transcription
  console.log('STT raw response:', typeof sttResponse, Object.keys(sttResponse || {}));
  const transcription = sttResponse && (sttResponse.text || sttResponse.transcript || '') || '';
  console.log(`Transcription: "${transcription}"`);

    // Send transcription back to client
    ws.send(JSON.stringify({
      type: 'transcription',
      text: transcription,
      timestamp: Date.now()
    }));

    // If we have a transcription, generate a response
    if (transcription.trim()) {
      await generateResponse(ws, transcription, env);
    }

    // Clear buffer after processing
    session.audioBuffer = [];

  } catch (error) {
    console.error('Audio processing error:', error?.message, error?.stack);
    ws.send(JSON.stringify({
      type: 'error',
      message: 'Failed to process audio',
      error: {
        message: error?.message || String(error),
        stack: (error && error.stack) ? String(error.stack).split('\n').slice(0,5).join('\n') : undefined
      }
    }));
  } finally {
    session.isProcessing = false;
  }
}

async function generateResponse(ws, userText, env) {
  try {
    // Simple response generation (in real app, you'd use LLM)
    const responses = [
      "I understand. Can you tell me more?",
      "That's interesting. How can I help you?",
      "Thank you for that information. What else would you like to know?",
      "I see. Let me help you with that."
    ];

    const responseText = responses[Math.floor(Math.random() * responses.length)];

    // Send text response
    ws.send(JSON.stringify({
      type: 'response_text',
      text: responseText,
      timestamp: Date.now()
    }));

    // Generate speech from text using Workers AI TTS
    const ttsResponse = await withTimeout(env.AI.run('@cf/deepgram/aura-1', {
      text: responseText,
      language: 'en'
    }), 15000);

    // Send audio response back
    if (ttsResponse.audio) {
      ws.send(JSON.stringify({
        type: 'response_audio',
        audio: Array.from(ttsResponse.audio),
        timestamp: Date.now()
      }));
    }

  } catch (error) {
    console.error('Response generation error:', error?.message, error?.stack);
    ws.send(JSON.stringify({
      type: 'error',
      message: 'Failed to generate response',
      error: {
        message: error?.message || String(error),
        stack: (error && error.stack) ? String(error.stack).split('\n').slice(0,5).join('\n') : undefined
      }
    }));
  }
}