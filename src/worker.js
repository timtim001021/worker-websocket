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

      // Initialize session state
      const session = {
        id: crypto.randomUUID(),
        audioBuffer: [],
        lastActivity: Date.now(),
        isProcessing: false
      };

      console.log(`New WebSocket session: ${session.id}`);

        // Handle incoming messages (non-blocking): do not await long-running work inside the event handler
        server.addEventListener('message', (event) => {
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
            }
          } catch (error) {
            console.error('Message handling error:', error?.message, error?.stack);
            try { server.send(JSON.stringify({ type: 'error', message: 'Failed to process message', error: { message: error?.message } })); } catch(e){}
          }

          session.lastActivity = Date.now();
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

    // Helper: wrap a promise with a timeout to avoid indefinite hangs
    const withTimeout = (p, ms) => Promise.race([
      p,
      new Promise((_, rej) => setTimeout(() => rej(new Error('AI.run timed out')), ms))
    ]);

    // Send WAV container to Workers AI for speech-to-text.
    const sttResponse = await withTimeout(env.AI.run('@cf/openai/whisper', {
      audio: [...wavBytes]
    }), 20000);

    // Extract transcription
    const transcription = sttResponse.text || '';
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