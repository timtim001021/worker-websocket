#!/usr/bin/env python3
"""
Quick WebSocket test with SSL verification disabled
"""

import asyncio
import websockets
import json
import ssl

async def test_worker():
    # Create SSL context that doesn't verify certificates
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    websocket_url = "wss://solitary-boat-0723.timtimtim001021.workers.dev"
    
    try:
        print("🔗 Connecting to:", websocket_url)
        async with websockets.connect(websocket_url, ssl=ssl_context) as websocket:
            print("✅ Connected successfully!")
            
            # Send a test message
            test_message = {
                "type": "audio_chunk",
                "data": "dGVzdCBhdWRpbyBkYXRh",  # base64 encoded "test audio data"
                "session_id": "test-session-123"
            }
            
            await websocket.send(json.dumps(test_message))
            print("📤 Sent test audio chunk")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print("📥 Received response:", response)
            except asyncio.TimeoutError:
                print("⏰ No response received within 5 seconds")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_worker())