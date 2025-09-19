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

      // Handle incoming messages
      server.addEventListener('message', async (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === 'audio_chunk') {
            // Handle streaming audio chunk
            await handleAudioChunk(server, data, session, env);
          } else if (data.type === 'end_stream') {
            // Process accumulated audio
            await processAudioBuffer(server, session, env);
          } else if (data.type === 'ping') {
            // Keep-alive
            server.send(JSON.stringify({ type: 'pong', timestamp: Date.now() }));
          }

          session.lastActivity = Date.now();
        } catch (error) {
          console.error('Message handling error:', error);
          server.send(JSON.stringify({
            type: 'error',
            message: 'Failed to process message'
          }));
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

async function handleAudioChunk(ws, data, session, env) {
  // Add audio chunk to buffer
  session.audioBuffer.push(...data.audio);

  // Send acknowledgment
  ws.send(JSON.stringify({
    type: 'chunk_received',
    chunk_size: data.audio.length,
    buffer_size: session.audioBuffer.length
  }));

  // Process if buffer is getting large or if we detect speech end
  if (session.audioBuffer.length > 16000 * 2) { // ~2 seconds at 16kHz
    await processAudioBuffer(ws, session, env);
  }
}

async function processAudioBuffer(ws, session, env) {
  if (session.isProcessing || session.audioBuffer.length === 0) {
    return;
  }

  session.isProcessing = true;

  try {
    // Convert buffer to Uint8Array
    const audioData = new Uint8Array(session.audioBuffer);

    console.log(`Processing ${audioData.length} bytes of audio for session ${session.id}`);

    // Send to Workers AI for speech-to-text
    const sttResponse = await env.AI.run('@cf/openai/whisper', {
      audio: [...audioData]
    });

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
    console.error('Audio processing error:', error);
    ws.send(JSON.stringify({
      type: 'error',
      message: 'Failed to process audio'
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
    const ttsResponse = await env.AI.run('@cf/deepgram/aura-1', {
      text: responseText,
      language: 'en'
    });

    // Send audio response back
    if (ttsResponse.audio) {
      ws.send(JSON.stringify({
        type: 'response_audio',
        audio: Array.from(ttsResponse.audio),
        timestamp: Date.now()
      }));
    }

  } catch (error) {
    console.error('Response generation error:', error);
    ws.send(JSON.stringify({
      type: 'error',
      message: 'Failed to generate response'
    }));
  }
}