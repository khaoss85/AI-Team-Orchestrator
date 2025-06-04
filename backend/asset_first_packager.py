from datetime import datetime
from typing import Dict, Any, List, Optional

from models import ActionableDeliverable, ExtractedAsset


class AssetFirstDeliverablePackager:
    """Create deliverables that start directly with concrete assets."""

    async def create_asset_first_deliverable(
        self,
        workspace_id: str,
        workspace_goal: str,
        deliverable_analysis: Dict[str, Any],
        extracted_assets: Dict[str, Any],
        completed_tasks: List[Dict],
        quality_analysis: Optional[Dict] = None,
    ) -> ActionableDeliverable:
        """Return an asset-first deliverable using provided assets."""

        actionable_assets = {}
        for aid, asset in extracted_assets.items():
            actionable_assets[aid] = ExtractedAsset(
                asset_name=asset.get("asset_type", "business_asset"),
                asset_data=asset.get("asset_data", {}),
                source_task_id=asset.get("source_task_id", ""),
                extraction_method=asset.get("extraction_method", "asset_first"),
                validation_score=asset.get("quality_score", 0.0),
                actionability_score=asset.get("actionability_score", 0.0),
                ready_to_use=asset.get("ready_to_use", False),
            )

        summary = (
            f"Asset-first deliverable for goal: {workspace_goal}. "
            f"{len(actionable_assets)} assets included."
        )
        usage = {aid: "Use this asset directly." for aid in actionable_assets}
        next_steps = ["Use the provided assets immediately to continue your project."]

        return ActionableDeliverable(
            workspace_id=workspace_id,
            deliverable_id=f"asset_first_{workspace_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            meta={"deliverable_type": "asset_first_package"},
            executive_summary=summary,
            actionable_assets=actionable_assets,
            usage_guide=usage,
            next_steps=next_steps,
            automation_ready=True,
            actionability_score=95,
        )
