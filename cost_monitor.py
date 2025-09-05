#!/usr/bin/env python3
import os
import asyncio
from datetime import datetime
from services.openai_usage_api_client import get_usage_client

async def monitor_costs():
    client = get_usage_client()
    while True:
        usage = await client.get_today_usage()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Today's cost: ${usage.total_cost:.4f} | Tokens: {usage.total_tokens:,}")
        
        if usage.total_cost > 5.0:
            print("⚠️ DAILY LIMIT EXCEEDED - SHUTTING DOWN AI SERVICES")
            os._exit(1)
        
        await asyncio.sleep(60)  # Check every minute

if __name__ == "__main__":
    print("Starting cost monitor...")
    asyncio.run(monitor_costs())
