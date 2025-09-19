#!/usr/bin/env python3
"""
Test OpenAI Realtime mode connection
"""
import asyncio
import websockets
import json

async def test_openai_mode():
    url = 'ws://localhost:8080/proxy'
    print('Testing OpenAI Realtime mode...')
    
    try:
        async with websockets.connect(url) as ws:
            print('Connected to proxy in OpenAI mode')
            
            # Send a simple session configuration
            session_update = {
                "type": "session.update",
                "session": {
                    "modalities": ["text", "audio"],
                    "instructions": "You are a helpful assistant.",
                    "voice": "alloy",
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                    "input_audio_transcription": {
                        "model": "whisper-1"
                    }
                }
            }
            
            await ws.send(json.dumps(session_update))
            print('Sent session update')
            
            # Wait for response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                print(f'Received response: {response[:200]}...')
            except asyncio.TimeoutError:
                print('Timeout waiting for OpenAI response')
            except Exception as e:
                print(f'Error receiving: {e}')
                
    except Exception as e:
        print(f'Connection error: {e}')

if __name__ == '__main__':
    asyncio.run(test_openai_mode())