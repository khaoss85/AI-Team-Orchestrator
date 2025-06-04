import asyncio
import sys

sys.path.insert(0, "backend")
from asset_first_packager import AssetFirstDeliverablePackager


async def _create_sample():
    packager = AssetFirstDeliverablePackager()
    assets = {
        "a1": {
            "asset_type": "contact_database",
            "asset_data": {"contacts": [{"name": "A", "email": "a@b.com"}]},
            "source_task_id": "1",
            "ready_to_use": True,
        }
    }
    return await packager.create_asset_first_deliverable(
        "ws1",
        "Collect contacts",
        {},
        assets,
        [],
    )


def test_asset_first_packager():
    deliverable = asyncio.run(_create_sample())
    assert deliverable.meta["deliverable_type"] == "asset_first_package"
    assert "a1" in deliverable.actionable_assets
    assert deliverable.actionable_assets["a1"].ready_to_use
