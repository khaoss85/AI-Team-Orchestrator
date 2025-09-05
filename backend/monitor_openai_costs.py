#!/usr/bin/env python3
"""
Real-time OpenAI Cost Monitor
Tracks API usage and displays cost consumption in real-time
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent))

async def monitor_costs():
    """Monitor OpenAI costs in real-time"""
    
    print("=" * 60)
    print("OPENAI COST MONITOR - REAL-TIME TRACKING")
    print("=" * 60)
    print()
    print("Press Ctrl+C to stop monitoring")
    print()
    
    # Import here to ensure backend is in path
    from services.openai_usage_api_client import get_usage_client
    
    client = get_usage_client()
    
    # Track previous values for rate calculation
    previous_cost = 0.0
    previous_tokens = 0
    previous_time = datetime.now()
    
    # Cost thresholds
    WARNING_THRESHOLD = 3.0  # Warn at $3/day
    CRITICAL_THRESHOLD = 5.0  # Critical at $5/day
    
    while True:
        try:
            # Get current usage
            usage = await client.get_today_usage()
            current_time = datetime.now()
            
            # Calculate rates
            time_delta = (current_time - previous_time).total_seconds()
            if time_delta > 0:
                cost_rate = (usage.total_cost - previous_cost) / time_delta * 3600  # $/hour
                token_rate = (usage.total_tokens - previous_tokens) / time_delta * 60  # tokens/min
            else:
                cost_rate = 0.0
                token_rate = 0.0
            
            # Determine status
            if usage.total_cost >= CRITICAL_THRESHOLD:
                status = "🔴 CRITICAL"
                status_color = "\033[91m"  # Red
            elif usage.total_cost >= WARNING_THRESHOLD:
                status = "🟡 WARNING"
                status_color = "\033[93m"  # Yellow
            else:
                status = "🟢 NORMAL"
                status_color = "\033[92m"  # Green
            
            # Clear line and print update
            print(f"\r{status_color}[{current_time.strftime('%H:%M:%S')}] {status}\033[0m | "
                  f"Today: ${usage.total_cost:.4f} | "
                  f"Tokens: {usage.total_tokens:,} | "
                  f"Rate: ${cost_rate:.2f}/hr | "
                  f"{token_rate:.0f} tok/min", end="", flush=True)
            
            # Alert if critical
            if usage.total_cost >= CRITICAL_THRESHOLD:
                print()
                print("\n" + "=" * 60)
                print("⚠️  DAILY COST LIMIT EXCEEDED!")
                print(f"Current cost: ${usage.total_cost:.4f}")
                print("Recommendation: Review URGENT_COST_ANALYSIS_REPORT.md")
                print("=" * 60)
                
                # Check if we should auto-shutdown
                if os.getenv("AI_COST_CIRCUIT_BREAKER", "false").lower() == "true":
                    print("\n🛑 CIRCUIT BREAKER TRIGGERED - SHUTTING DOWN AI SERVICES")
                    # Create shutdown signal file
                    Path("COST_SHUTDOWN_TRIGGERED").touch()
                    break
            
            # Update previous values
            previous_cost = usage.total_cost
            previous_tokens = usage.total_tokens
            previous_time = current_time
            
            # Wait before next check
            await asyncio.sleep(10)  # Check every 10 seconds
            
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user.")
            break
        except Exception as e:
            print(f"\n❌ Error getting usage data: {e}")
            await asyncio.sleep(30)  # Wait longer on error
    
    # Final summary
    print("\n" + "=" * 60)
    print("MONITORING SESSION SUMMARY")
    print("-" * 60)
    print(f"Final cost today: ${usage.total_cost:.4f}")
    print(f"Total tokens used: {usage.total_tokens:,}")
    print(f"Emergency controls active: {os.getenv('AI_COST_CIRCUIT_BREAKER', 'false')}")
    print("=" * 60)

if __name__ == "__main__":
    try:
        asyncio.run(monitor_costs())
    except KeyboardInterrupt:
        print("\nMonitor stopped.")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)