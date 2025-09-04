#!/usr/bin/env python3
"""
Test script for WebSocket quota endpoint
"""

import asyncio
import websockets
import json

async def test_quota_websocket():
    uri = "ws://localhost:8000/api/quota/ws"
    
    try:
        print(f"🔌 Connecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to quota WebSocket!")
            
            # Wait for initial message
            initial_message = await websocket.recv()
            data = json.loads(initial_message)
            print(f"📊 Initial status: {data}")
            
            # Send ping
            ping_message = json.dumps({"type": "ping"})
            await websocket.send(ping_message)
            print("📤 Sent ping")
            
            # Wait for pong
            response = await websocket.recv()
            pong_data = json.loads(response)
            print(f"📥 Received: {pong_data}")
            
            # Request status
            status_request = json.dumps({"type": "request_status"})
            await websocket.send(status_request)
            print("📤 Sent status request")
            
            # Wait for status response
            status_response = await websocket.recv()
            status_data = json.loads(status_response)
            print(f"📊 Status update: {status_data}")
            
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_quota_websocket())