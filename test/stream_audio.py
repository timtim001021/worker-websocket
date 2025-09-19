#!/usr/bin/env python3
"""
Stream a WAV file (or generated tone) to the deployed worker as real audio chunks.

Usage:
  python3 stream_audio.py [--file path/to/file.wav] [--url wss://...] [--chunk-samples N]

If no file is provided, a 1s 440Hz sine wave (16kHz, mono, 16-bit) is generated.
"""

import argparse
import asyncio
import websockets
import ssl
import wave
import struct
import math
import json
import os

DEFAULT_URL = "wss://solitary-boat-0723.timtimtim001021.workers.dev"
CHUNK_SAMPLES = 1600  # 100ms at 16kHz


def generate_sine(duration_s=1.0, freq=440, sample_rate=16000):
    samples = []
    total = int(duration_s * sample_rate)
    for n in range(total):
        t = n / sample_rate
        # amplitude for 16-bit PCM
        val = int(32767 * 0.2 * math.sin(2 * math.pi * freq * t))
        samples.append(val)
    return samples, sample_rate


def read_wav_as_samples(path):
    with wave.open(path, 'rb') as wf:
        channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        nframes = wf.getnframes()
        raw = wf.readframes(nframes)

    if sampwidth != 2:
        raise RuntimeError(f"Unsupported sample width: {sampwidth*8} bits - only 16-bit supported")

    # unpack little-endian signed 16-bit
    fmt = '<' + 'h' * (len(raw)//2)
    ints = list(struct.unpack(fmt, raw))

    # If stereo, pick the first channel
    if channels == 2:
        ints = ints[0::2]

    return ints, framerate


async def stream_samples(samples, sample_rate, websocket_url, chunk_samples=CHUNK_SAMPLES, session_id="stream-session"):
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    print(f"Connecting to {websocket_url} (resampling not performed; expected 16000 Hz)")
    async with websockets.connect(websocket_url, ssl=ssl_context) as ws:
        print("Connected")
        pos = 0
        # send chunks
        while pos < len(samples):
            chunk = samples[pos:pos+chunk_samples]
            msg = {
                "type": "audio_chunk",
                "audio": chunk,
                "session_id": session_id
            }
            await ws.send(json.dumps(msg))
            print(f"Sent chunk samples {pos}-{pos+len(chunk)} ({len(chunk)} samples)")
            # receive optional ack
            try:
                resp = await asyncio.wait_for(ws.recv(), timeout=2.0)
                print("Received:", resp)
            except asyncio.TimeoutError:
                print("No immediate response")
            pos += chunk_samples
            await asyncio.sleep(0.05)  # small delay to simulate streaming

        # send end_stream
        await ws.send(json.dumps({"type": "end_stream", "session_id": session_id}))
        print("Sent end_stream, waiting for processing response...")
        try:
            resp = await asyncio.wait_for(ws.recv(), timeout=15.0)
            print("Processing response:", resp)
        except asyncio.TimeoutError:
            print("No processing response received")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', '-f', help='Path to WAV file (16-bit PCM, mono or stereo, 16kHz recommended)')
    parser.add_argument('--url', '-u', default=os.environ.get('WORKER_WS_URL', DEFAULT_URL), help='WebSocket URL')
    parser.add_argument('--chunk-samples', type=int, default=CHUNK_SAMPLES)
    parser.add_argument('--session-id', default='stream-session')
    args = parser.parse_args()

    if args.file:
        print(f"Reading WAV file {args.file}")
        samples, sr = read_wav_as_samples(args.file)
        print(f"Read {len(samples)} samples at {sr} Hz")
    else:
        print("No file provided; generating 1s sine wave (440Hz)")
        samples, sr = generate_sine(duration_s=1.0)
        print(f"Generated {len(samples)} samples at {sr} Hz")

    if sr != 16000:
        print("Warning: sample rate is not 16000 Hz. Worker assumes 16kHz. Results may vary.")

    asyncio.run(stream_samples(samples, sr, args.url, chunk_samples=args.chunk_samples, session_id=args.session_id))


if __name__ == '__main__':
    main()
