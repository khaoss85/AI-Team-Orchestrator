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
        """Return an asset-first deliverable focusing on concrete, actionable assets."""

        # Categorize and prioritize assets
        immediate_assets = {}
        development_assets = {}
        
        for aid, asset in extracted_assets.items():
            asset_quality = asset.get("quality_score", 0.0)
            asset_actionability = asset.get("actionability_score", 0.0)
            ready_to_use = asset.get("ready_to_use", False)
            
            # Create enhanced ExtractedAsset
            extracted_asset = ExtractedAsset(
                asset_name=asset.get("asset_type", "business_asset"),
                asset_data=asset.get("asset_data", {}),
                source_task_id=asset.get("source_task_id", ""),
                extraction_method=asset.get("extraction_method", "asset_first"),
                validation_score=asset_quality,
                actionability_score=asset_actionability,
                ready_to_use=ready_to_use,
            )
            
            # Classify by actionability
            if ready_to_use and asset_quality >= 0.6 and asset_actionability >= 0.7:
                immediate_assets[aid] = extracted_asset
            else:
                development_assets[aid] = extracted_asset

        # Combine all assets
        actionable_assets = {**immediate_assets, **development_assets}
        
        # Create focused executive summary
        business_focus = deliverable_analysis.get('business_value_focus', 'business growth')
        total_assets = len(actionable_assets)
        immediate_count = len(immediate_assets)
        
        summary = self._create_focused_summary(
            workspace_goal, business_focus, total_assets, immediate_count
        )
        
        # Create detailed usage guide
        usage_guide = self._create_detailed_usage_guide(
            immediate_assets, development_assets, business_focus
        )
        
        # Create specific next steps
        next_steps = self._create_actionable_next_steps(
            immediate_assets, development_assets, workspace_goal
        )
        
        # Calculate realistic actionability score
        overall_actionability = self._calculate_actionability_score(actionable_assets)

        return ActionableDeliverable(
            workspace_id=workspace_id,
            deliverable_id=f"asset_first_{workspace_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            meta={
                "deliverable_type": "asset_first_package",
                "immediate_assets": immediate_count,
                "total_assets": total_assets,
                "business_focus": business_focus
            },
            executive_summary=summary,
            actionable_assets=actionable_assets,
            usage_guide=usage_guide,
            next_steps=next_steps,
            automation_ready=immediate_count > 0,
            actionability_score=overall_actionability,
        )
    
    def _create_focused_summary(self, workspace_goal: str, business_focus: str, total_assets: int, immediate_count: int) -> str:
        """Create a focused, business-oriented summary"""
        
        if immediate_count > 0:
            readiness_text = f"{immediate_count} ready-to-use assets for immediate implementation"
        else:
            readiness_text = f"{total_assets} assets requiring customization before use"
            
        return (
            f"🎯 ASSET-READY DELIVERABLE: {readiness_text} to achieve '{workspace_goal}'. "
            f"Focus: {business_focus}. "
            f"Implementation tier: {'IMMEDIATE' if immediate_count >= total_assets/2 else 'DEVELOPMENT REQUIRED'}."
        )
    
    def _create_detailed_usage_guide(self, immediate_assets: Dict, development_assets: Dict, business_focus: str) -> Dict[str, str]:
        """Create detailed usage instructions for each asset"""
        
        usage_guide = {}
        
        for aid, asset in immediate_assets.items():
            asset_type = asset.asset_name
            usage_guide[aid] = (
                f"IMMEDIATE USE: This {asset_type} is ready for deployment. "
                f"Can be used directly to support {business_focus}. "
                f"No additional development required."
            )
        
        for aid, asset in development_assets.items():
            asset_type = asset.asset_name
            usage_guide[aid] = (
                f"DEVELOPMENT NEEDED: This {asset_type} requires customization before use. "
                f"Review content, adapt to your specific {business_focus} needs, "
                f"then implement in your workflow."
            )
        
        return usage_guide
    
    def _create_actionable_next_steps(self, immediate_assets: Dict, development_assets: Dict, workspace_goal: str) -> List[str]:
        """Create specific, actionable next steps"""
        
        next_steps = []
        
        if immediate_assets:
            next_steps.append(
                f"🚀 WEEK 1: Deploy {len(immediate_assets)} ready assets: "
                f"{', '.join([asset.asset_name for asset in list(immediate_assets.values())[:3]])}"
                f"{'...' if len(immediate_assets) > 3 else ''}"
            )
        
        if development_assets:
            next_steps.append(
                f"🔧 WEEK 2-3: Customize {len(development_assets)} development assets: "
                f"{', '.join([asset.asset_name for asset in list(development_assets.values())[:3]])}"
                f"{'...' if len(development_assets) > 3 else ''}"
            )
        
        # Add specific implementation steps
        next_steps.extend([
            f"📊 WEEK 2: Measure initial impact of deployed assets on '{workspace_goal}'",
            f"🔄 WEEK 4: Iterate on asset performance and optimize for better results",
            f"📈 MONTH 2: Scale successful assets and develop additional supporting materials"
        ])
        
        return next_steps
    
    def _calculate_actionability_score(self, actionable_assets: Dict) -> int:
        """Calculate realistic actionability score based on asset readiness"""
        
        if not actionable_assets:
            return 0
        
        total_score = 0
        for asset in actionable_assets.values():
            score = (asset.actionability_score * 0.5) + (asset.validation_score * 0.3)
            if asset.ready_to_use:
                score += 0.2
            total_score += score
        
        avg_score = total_score / len(actionable_assets)
        return min(100, int(avg_score * 100))
