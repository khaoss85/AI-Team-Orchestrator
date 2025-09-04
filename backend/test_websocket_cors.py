#!/usr/bin/env python3
"""
Test WebSocket connection with CORS headers to verify frontend connectivity
"""

import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/api/quota/ws"
    
    # Test with Origin header from frontend
    headers = {
        "Origin": "http://localhost:3001"
    }
    
    try:
        print(f"🔌 Connecting to {uri} with Origin: http://localhost:3001")
        
        # WebSockets library uses 'origin' parameter directly
        async with websockets.connect(uri, origin="http://localhost:3001") as websocket:
            print("✅ WebSocket connected successfully with CORS headers!")
            
            # Wait for initial message
            message = await asyncio.wait_for(websocket.recv(), timeout=5)
            data = json.loads(message)
            print(f"📊 Initial message received: {json.dumps(data, indent=2)}")
            
            # Keep connection open for a moment
            await asyncio.sleep(2)
            
            print("✅ WebSocket test completed successfully!")
            
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_websocket())
    exit(0 if success else 1)