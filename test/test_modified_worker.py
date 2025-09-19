#!/usr/bin/env python3
"""
Test script for the modified Cloudflare Worker that processes audio data
"""

import requests
import json
import time
import wave
import struct

def create_simple_audio_phrase():
    """Create a simple audio sample that should transcribe to something recognizable"""
    sample_rate = 16000
    duration = 1  # 1 second
    frequency = 800  # Hz (higher frequency for clearer sound)

    samples = []
    for i in range(int(sample_rate * duration)):
        # Create a simple tone that might be recognizable
        t = i / sample_rate
        # Modulate the amplitude to simulate speech patterns
        amplitude = 0.3 + 0.2 * ((i // 1000) % 2)  # Alternating amplitude
        sample = int(32767 * amplitude * (i % 2 - 0.5) * 2)  # Square wave
        samples.append(sample)

    # Convert to bytes (16-bit PCM)
    audio_bytes = b''
    for sample in samples:
        audio_bytes += struct.pack('<h', sample)

    return audio_bytes

def test_modified_worker(worker_url):
    """Test the modified worker with different scenarios"""
    print(f"🔍 Testing modified worker: {worker_url}")
    print("=" * 60)

    # Test 1: GET request (should still work with built-in sample)
    print("1️⃣ GET Request (built-in sample):")
    try:
        response = requests.get(worker_url, timeout=30)
        result = response.json()

        print(f"   Status: {response.status_code}")
        print(f"   Method: {result.get('method', 'unknown')}")
        print(f"   Source: {result.get('source', 'unknown')}")

        if 'response' in result and 'text' in result['response']:
            transcription = result['response']['text']
            print(f"   🎯 Transcription: '{transcription[:80]}...'")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    print()

    # Test 2: POST with no audio data
    print("2️⃣ POST Request (no audio data):")
    try:
        response = requests.post(
            worker_url,
            json={},
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        result = response.json()

        print(f"   Status: {response.status_code}")
        print(f"   Method: {result.get('method', 'unknown')}")
        print(f"   Source: {result.get('source', 'unknown')}")

        if 'response' in result and 'text' in result['response']:
            transcription = result['response']['text']
            print(f"   🎯 Transcription: '{transcription[:80]}...'")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    print()

    # Test 3: POST with simple generated audio
    print("3️⃣ POST Request (simple generated audio):")
    try:
        audio_data = create_simple_audio_phrase()
        audio_array = list(audio_data)

        payload = {"audio": audio_array}

        response = requests.post(
            worker_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        result = response.json()

        print(f"   Status: {response.status_code}")
        print(f"   Method: {result.get('method', 'unknown')}")
        print(f"   Source: {result.get('source', 'unknown')}")
        print(f"   Audio bytes: {result.get('audio_bytes', 'unknown')}")

        if 'response' in result and 'text' in result['response']:
            transcription = result['response']['text']
            print(f"   🎯 Transcription: '{transcription}'")
        else:
            print("   📄 Full response:")
            print(json.dumps(result, indent=2))

    except Exception as e:
        print(f"   ❌ Error: {e}")

    print()

    # Test 4: POST with small WAV file chunk
    print("4️⃣ POST Request (small WAV chunk):")
    try:
        # Read just the first 10KB of the WAV file
        with open('../samples/OSR_us_000_0011_8k.wav', 'rb') as f:
            audio_chunk = f.read(10000)  # 10KB chunk

        audio_array = list(audio_chunk)
        payload = {"audio": audio_array}

        response = requests.post(
            worker_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        result = response.json()

        print(f"   Status: {response.status_code}")
        print(f"   Method: {result.get('method', 'unknown')}")
        print(f"   Source: {result.get('source', 'unknown')}")
        print(f"   Audio bytes: {result.get('audio_bytes', 'unknown')}")

        if 'response' in result and 'text' in result['response']:
            transcription = result['response']['text']
            print(f"   🎯 Transcription: '{transcription[:100]}...'")
        else:
            print("   📄 Full response:")
            print(json.dumps(result, indent=2))

    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    worker_url = "https://solitary-boat-0723.timtimtim001021.workers.dev"
    test_modified_worker(worker_url)