#!/usr/bin/env python3
"""
Test with proper audio chunk format
"""

import asyncio
import websockets
import json
import ssl
import base64

async def test_with_proper_format():
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    websocket_url = "wss://solitary-boat-0723.timtimtim001021.workers.dev"
    
    try:
        print("🔗 Connecting to:", websocket_url)
        async with websockets.connect(websocket_url, ssl=ssl_context) as websocket:
            print("✅ Connected successfully!")
            
            # Generate some fake audio data (silence)
            # This is 1000 bytes of silence (16-bit, mono, 16kHz would be ~30ms)
            fake_audio = b'\x00' * 1000
            audio_b64 = base64.b64encode(fake_audio).decode('utf-8')
            
            message = {
                "type": "audio_chunk", 
                "audio_data": audio_b64,
                "session_id": "test-session-456",
                "format": "raw_pcm_16khz_mono"
            }
            
            await websocket.send(json.dumps(message))
            print("📤 Sent properly formatted audio chunk")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                print("📥 Received response:", response)
                
                # Try to send another chunk
                await asyncio.sleep(0.2)  # 200ms delay like real streaming
                await websocket.send(json.dumps(message))
                print("📤 Sent second audio chunk")
                
                response2 = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                print("📥 Received second response:", response2)
                
            except asyncio.TimeoutError:
                print("⏰ No response received within timeout")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_with_proper_format())