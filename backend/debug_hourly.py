#!/usr/bin/env python3
import asyncio
from services.openai_usage_api_client import OpenAIUsageAPIClient

async def debug():
    client = OpenAIUsageAPIClient()
    usage = await client.get_today_usage()
    print(f"Hourly breakdown type: {type(usage.hourly_breakdown)}")
    print(f"Hourly breakdown value: {usage.hourly_breakdown}")
    if usage.hourly_breakdown:
        for key, value in usage.hourly_breakdown.items():
            print(f"  Key: {repr(key)}, Value: {value}")
            break

asyncio.run(debug())