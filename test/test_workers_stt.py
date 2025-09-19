#!/usr/bin/env python3
"""
Test script for Cloudflare Workers AI Speech-to-Text
Tests the deployed worker at: solitary-boat-0723.timtimtim001021.workers.dev
"""

import requests
import json
import time
import os

def test_worker_with_audio_file(worker_url, audio_file_path):
    """Test the worker by sending an audio file"""
    print(f"Testing worker: {worker_url}")
    print(f"Audio file: {audio_file_path}")
    
    if not os.path.exists(audio_file_path):
        print(f"❌ Audio file not found: {audio_file_path}")
        return
    
    # Read audio file as binary
    with open(audio_file_path, 'rb') as f:
        audio_data = f.read()
    
    print(f"📁 Audio file size: {len(audio_data)} bytes")
    
    # Prepare the request - convert binary data to array of bytes
    payload = {
        "audio": list(audio_data)
    }
    
    print("🚀 Sending request to worker...")
    start_time = time.time()
    
    try:
        # Send POST request with audio data
        response = requests.post(
            worker_url,
            json=payload,
            headers={
                'Content-Type': 'application/json'
            },
            timeout=30
        )
        
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        
        print(f"⏱️  Response time: {latency:.2f}ms")
        print(f"📡 Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            
            # Print the transcription result
            if 'response' in result and 'text' in result['response']:
                transcription = result['response']['text']
                print(f"🎯 Transcription: '{transcription}'")
            else:
                print("📄 Full response:")
                print(json.dumps(result, indent=2))
        else:
            print(f"❌ Error response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out after 30 seconds")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        print(f"Raw response: {response.text}")

def test_worker_get_request(worker_url):
    """Test the worker with a simple GET request (uses the built-in audio sample)"""
    print(f"🔍 Testing worker with GET request: {worker_url}")
    
    start_time = time.time()
    
    try:
        response = requests.get(worker_url, timeout=30)
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        
        print(f"⏱️  Response time: {latency:.2f}ms")
        print(f"📡 Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            
            # Print the transcription result
            if 'response' in result and 'text' in result['response']:
                transcription = result['response']['text']
                print(f"🎯 Transcription: '{transcription}'")
            else:
                print("📄 Full response:")
                print(json.dumps(result, indent=2))
        else:
            print(f"❌ Error response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    worker_url = "https://solitary-boat-0723.timtimtim001021.workers.dev"
    audio_file = "../samples/OSR_us_000_0011_8k.wav"
    
    print("=" * 60)
    print("🤖 Cloudflare Workers AI Speech-to-Text Test")
    print("=" * 60)
    
    # Test 1: GET request (uses worker's built-in sample)
    print("\n1️⃣ Testing with built-in audio sample (GET request):")
    test_worker_get_request(worker_url)
    
    # Test 2: POST request with our audio file
    print(f"\n2️⃣ Testing with local audio file (POST request):")
    test_worker_with_audio_file(worker_url, audio_file)
    
    print("\n✨ Test completed!")