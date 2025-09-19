#!/usr/bin/env python3
"""
Test script to send actual audio data to the worker
"""

import requests
import json
import time
import wave
import struct

def create_test_audio():
    """Create a simple test audio file with a spoken phrase"""
    # Create a simple sine wave that sounds like speech
    sample_rate = 16000
    duration = 2  # seconds
    frequency = 440  # Hz

    # Generate sine wave
    samples = []
    for i in range(int(sample_rate * duration)):
        # Create a sine wave with some variation to simulate speech
        t = i / sample_rate
        wave_value = 0.5 * (1 + 0.3 * (i % 100) / 100) * (0.8 + 0.2 * (i % 50) / 50)
        sample = int(32767 * wave_value)
        samples.append(sample)

    # Convert to bytes (16-bit PCM)
    audio_bytes = b''
    for sample in samples:
        audio_bytes += struct.pack('<h', sample)

    return audio_bytes

def test_with_generated_audio(worker_url):
    """Test the worker with generated audio data"""
    print("🎵 Testing with generated audio data...")

    # Create test audio
    audio_data = create_test_audio()
    print(f"   Generated audio: {len(audio_data)} bytes")

    # Convert to array format expected by worker
    audio_array = list(audio_data)

    payload = {"audio": audio_array}

    try:
        start_time = time.time()
        response = requests.post(
            worker_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        end_time = time.time()
        latency = (end_time - start_time) * 1000

        print(f"   Status: {response.status_code}")
        print(f"   Latency: {latency:.2f}ms")

        if response.status_code == 200:
            result = response.json()
            print("   ✅ Success!")

            if 'response' in result and 'text' in result['response']:
                transcription = result['response']['text']
                print(f"   🎯 Transcription: '{transcription}'")
            else:
                print("   📄 Full response:")
                print(json.dumps(result, indent=2))
        else:
            print(f"   ❌ Error: {response.text}")

    except Exception as e:
        print(f"   ❌ Exception: {e}")

def test_with_real_audio_file(worker_url, audio_file_path):
    """Test with a real WAV file"""
    print(f"🎵 Testing with real audio file: {audio_file_path}")

    try:
        # Read WAV file
        with wave.open(audio_file_path, 'rb') as wav_file:
            # Get audio parameters
            sample_rate = wav_file.getframerate()
            num_channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()

            print(f"   Audio info: {sample_rate}Hz, {num_channels}ch, {sample_width*8}bit")

            # Read audio data
            audio_data = wav_file.readframes(wav_file.getnframes())
            print(f"   Audio size: {len(audio_data)} bytes")

            # Convert to array of bytes
            audio_array = list(audio_data)

            payload = {"audio": audio_array}

            start_time = time.time()
            response = requests.post(
                worker_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=60  # Longer timeout for larger files
            )
            end_time = time.time()
            latency = (end_time - start_time) * 1000

            print(f"   Status: {response.status_code}")
            print(f"   Latency: {latency:.2f}ms")

            if response.status_code == 200:
                result = response.json()
                print("   ✅ Success!")

                if 'response' in result and 'text' in result['response']:
                    transcription = result['response']['text']
                    print(f"   🎯 Transcription: '{transcription[:200]}...'")
                else:
                    print("   📄 Full response:")
                    print(json.dumps(result, indent=2))
            else:
                print(f"   ❌ Error: {response.text}")

    except Exception as e:
        print(f"   ❌ Exception: {e}")

if __name__ == "__main__":
    worker_url = "https://solitary-boat-0723.timtimtim001021.workers.dev"

    print("=" * 60)
    print("🔊 Audio Data Tests for Cloudflare Worker")
    print("=" * 60)

    # Test 1: Generated audio
    test_with_generated_audio(worker_url)
    print()

    # Test 2: Real audio file
    audio_file = "../samples/OSR_us_000_0011_8k.wav"
    test_with_real_audio_file(worker_url, audio_file)