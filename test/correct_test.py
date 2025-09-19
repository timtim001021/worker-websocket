#!/usr/bin/env python3
"""
Test with correct field names
"""

import asyncio
import websockets
import json
import ssl
import base64

async def test_correct_format():
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    websocket_url = "wss://solitary-boat-0723.timtimtim001021.workers.dev"
    
    try:
        print("🔗 Connecting to:", websocket_url)
        async with websockets.connect(websocket_url, ssl=ssl_context) as websocket:
            print("✅ Connected successfully!")
            
            # Generate some fake audio samples (array of numbers)
            # Simulating 16-bit PCM samples
            fake_audio_samples = [0] * 1600  # 1600 samples = 100ms at 16kHz
            
            message = {
                "type": "audio_chunk", 
                "audio": fake_audio_samples,  # Use "audio" not "audio_data"
                "session_id": "test-session-789"
            }
            
            await websocket.send(json.dumps(message))
            print("📤 Sent audio chunk with correct format")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                print("📥 Received response:", response)
                
                # Send end_stream to trigger processing
                end_message = {
                    "type": "end_stream",
                    "session_id": "test-session-789"
                }
                await websocket.send(json.dumps(end_message))
                print("📤 Sent end_stream message")
                
                response2 = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                print("📥 Received processing response:", response2)
                
            except asyncio.TimeoutError:
                print("⏰ No response received within timeout")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_correct_format())