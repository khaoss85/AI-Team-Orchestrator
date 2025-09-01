#!/usr/bin/env python3
"""
Test import of broadcast function
"""

try:
    from routes.websocket_assets import broadcast_goal_progress_update
    print("✅ Successfully imported broadcast_goal_progress_update")
    print(f"📍 Function location: {broadcast_goal_progress_update}")
except Exception as e:
    print(f"❌ Failed to import broadcast_goal_progress_update: {e}")
    import traceback
    traceback.print_exc()

try:
    import asyncio
    from database_asset_extensions import AssetDrivenDatabaseManager
    db = AssetDrivenDatabaseManager()
    print("✅ Successfully imported AssetDrivenDatabaseManager")
except Exception as e:
    print(f"❌ Failed to import AssetDrivenDatabaseManager: {e}")
    import traceback
    traceback.print_exc()