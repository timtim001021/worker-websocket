#!/usr/bin/env python3
"""
WebSocket client to test the real-world conversational worker
Simulates how a phone provider would connect and stream audio
"""

import asyncio
import websockets
import json
import time
import wave
import struct
import threading
import queue

class AudioStreamer:
    def __init__(self, websocket_url):
        self.websocket_url = websocket_url
        self.audio_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.is_connected = False

    async def connect(self):
        """Establish WebSocket connection"""
        try:
            self.websocket = await websockets.connect(self.websocket_url)
            self.is_connected = True
            print("🔗 Connected to WebSocket worker")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False

    async def send_audio_chunk(self, audio_data):
        """Send audio chunk to worker"""
        if not self.is_connected:
            return

        message = {
            "type": "audio_chunk",
            "audio": list(audio_data),
            "timestamp": time.time()
        }

        try:
            await self.websocket.send(json.dumps(message))
            print(f"📤 Sent audio chunk: {len(audio_data)} bytes")
        except Exception as e:
            print(f"❌ Send error: {e}")

    async def end_stream(self):
        """Signal end of audio stream"""
        if not self.is_connected:
            return

        message = {
            "type": "end_stream",
            "timestamp": time.time()
        }

        try:
            await self.websocket.send(json.dumps(message))
            print("🏁 Sent end stream signal")
        except Exception as e:
            print(f"❌ End stream error: {e}")

    async def receive_messages(self):
        """Receive and process messages from worker"""
        try:
            async for message in self.websocket:
                data = json.loads(message)

                if data['type'] == 'chunk_received':
                    print(f"✅ Chunk received: {data['chunk_size']} bytes")

                elif data['type'] == 'transcription':
                    transcription = data['text']
                    print(f"🎯 Transcription: '{transcription}'")

                elif data['type'] == 'response_text':
                    response_text = data['text']
                    print(f"💬 Response: '{response_text}'")

                elif data['type'] == 'response_audio':
                    audio_data = data['audio']
                    print(f"🔊 Received audio response: {len(audio_data)} bytes")

                elif data['type'] == 'error':
                    print(f"❌ Worker error: {data['message']}")

                elif data['type'] == 'pong':
                    print("🏓 Pong received")

                else:
                    print(f"📨 Unknown message type: {data['type']}")

        except Exception as e:
            print(f"❌ Receive error: {e}")
        finally:
            self.is_connected = False

    async def keep_alive(self):
        """Send periodic ping messages"""
        while self.is_connected:
            try:
                message = {
                    "type": "ping",
                    "timestamp": time.time()
                }
                await self.websocket.send(json.dumps(message))
                await asyncio.sleep(30)  # Ping every 30 seconds
            except Exception as e:
                print(f"❌ Ping error: {e}")
                break

def create_test_audio():
    """Create a simple test audio sample"""
    sample_rate = 16000
    duration = 1.5  # 1.5 seconds
    frequency = 440  # A note

    samples = []
    for i in range(int(sample_rate * duration)):
        # Create a sine wave with some variation
        t = i / sample_rate
        wave_value = 0.3 * (1 + 0.2 * (i % 100) / 100) * (0.8 + 0.2 * (i % 50) / 50)
        sample = int(32767 * wave_value)
        samples.append(sample)

    # Convert to bytes (16-bit PCM)
    audio_bytes = b''
    for sample in samples:
        audio_bytes += struct.pack('<h', sample)

    return audio_bytes

async def simulate_phone_call(streamer):
    """Simulate a phone call by streaming audio chunks"""
    print("📞 Simulating phone call...")

    # Create test audio
    test_audio = create_test_audio()
    chunk_size = 3200  # 200ms chunks at 16kHz

    # Stream audio in chunks
    for i in range(0, len(test_audio), chunk_size):
        chunk = test_audio[i:i + chunk_size]
        if chunk:
            await streamer.send_audio_chunk(chunk)
            await asyncio.sleep(0.2)  # Simulate real-time streaming

    # Signal end of stream
    await streamer.end_stream()

    # Wait a bit for processing
    await asyncio.sleep(3)

async def main():
    websocket_url = "wss://solitary-boat-0723.timtimtim001021.workers.dev"

    print("=" * 60)
    print("📞 Real-World WebSocket Audio Streaming Test")
    print("=" * 60)

    streamer = AudioStreamer(websocket_url)

    # Connect to worker
    if not await streamer.connect():
        return

    try:
        # Start message receiver
        receive_task = asyncio.create_task(streamer.receive_messages())

        # Start keep-alive pings
        ping_task = asyncio.create_task(streamer.keep_alive())

        # Simulate phone call
        await simulate_phone_call(streamer)

        # Wait for responses
        await asyncio.sleep(5)

        # Clean shutdown
        ping_task.cancel()
        receive_task.cancel()

    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if streamer.is_connected:
            await streamer.websocket.close()
        print("🔌 Connection closed")

if __name__ == "__main__":
    asyncio.run(main())