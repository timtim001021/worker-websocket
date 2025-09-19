#!/usr/bin/env python3
"""
Simple WebSocket connection test - just verify the worker accepts connections
"""

import asyncio
import websockets
import json

async def test_connection():
    """Test basic WebSocket connection"""
    uri = "wss://solitary-boat-0723.timtimtim001021.workers.dev"

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connection successful!")

            # Send a simple ping
            ping_msg = {"type": "ping", "timestamp": 1234567890}
            await websocket.send(json.dumps(ping_msg))
            print("📤 Sent ping message")

            # Wait for response
            response = await websocket.recv()
            data = json.loads(response)
            print(f"📨 Received: {data}")

            # Close connection
            await websocket.close()
            print("🔌 Connection closed")

    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    print("🔗 Testing WebSocket connection...")
    asyncio.run(test_connection())