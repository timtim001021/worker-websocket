#!/usr/bin/env python3
"""
Test the WebSocket worker with real WAV file chunks
"""

import asyncio
import websockets
import json
import time
import wave
import struct

async def stream_wav_file(websocket_url, wav_file_path):
    """Stream a WAV file in chunks to simulate real-time audio"""
    print(f"🎵 Streaming WAV file: {wav_file_path}")

    try:
        async with websockets.connect(websocket_url) as websocket:
            print("🔗 Connected to WebSocket worker")

            # Read WAV file
            with wave.open(wav_file_path, 'rb') as wav_file:
                sample_rate = wav_file.getframerate()
                num_channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()

                print(f"📊 Audio: {sample_rate}Hz, {num_channels}ch, {sample_width*8}bit")

                # Read audio in chunks (200ms at 8kHz = 1600 bytes)
                chunk_size = 1600

                chunk_count = 0
                while True:
                    audio_chunk = wav_file.readframes(chunk_size // (sample_width * num_channels))

                    if not audio_chunk:
                        break

                    # Convert to list of bytes for JSON
                    audio_bytes = list(audio_chunk)

                    # Send audio chunk
                    message = {
                        "type": "audio_chunk",
                        "audio": audio_bytes,
                        "chunk_id": chunk_count,
                        "timestamp": time.time()
                    }

                    await websocket.send(json.dumps(message))
                    print(f"📤 Sent chunk {chunk_count}: {len(audio_bytes)} bytes")

                    chunk_count += 1

                    # Simulate real-time streaming (200ms delay)
                    await asyncio.sleep(0.2)

                    # Receive acknowledgment
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        data = json.loads(response)
                        if data['type'] == 'chunk_received':
                            print(f"✅ Chunk {data.get('chunk_size', 0)} bytes received")
                    except asyncio.TimeoutError:
                        print("⏰ No acknowledgment received")

                # Send end of stream
                end_message = {
                    "type": "end_stream",
                    "total_chunks": chunk_count,
                    "timestamp": time.time()
                }

                await websocket.send(json.dumps(end_message))
                print(f"🏁 Sent end stream after {chunk_count} chunks")

                # Wait for final processing
                print("⏳ Waiting for transcription...")
                start_time = time.time()

                while time.time() - start_time < 10:  # Wait up to 10 seconds
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        data = json.loads(response)

                        if data['type'] == 'transcription':
                            transcription = data['text']
                            print(f"🎯 Final transcription: '{transcription}'")
                            break
                        elif data['type'] == 'response_text':
                            response_text = data['text']
                            print(f"💬 Response: '{response_text}'")
                        elif data['type'] == 'error':
                            print(f"❌ Error: {data['message']}")
                            break
                        else:
                            print(f"📨 Message: {data['type']}")

                    except asyncio.TimeoutError:
                        print("⏰ Timeout waiting for response")
                        break

    except Exception as e:
        print(f"❌ Error: {e}")

async def main():
    websocket_url = "wss://solitary-boat-0723.timtimtim001021.workers.dev"
    wav_file = "../samples/OSR_us_000_0011_8k.wav"

    print("=" * 60)
    print("🎵 WebSocket WAV File Streaming Test")
    print("=" * 60)

    await stream_wav_file(websocket_url, wav_file)

if __name__ == "__main__":
    asyncio.run(main())