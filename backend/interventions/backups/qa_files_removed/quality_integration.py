# backend/ai_quality_assurance/quality_integration.py

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class DynamicPromptEnhancer:
    """
    Migliora dinamicamente i prompt degli agent per aumentare la qualità dell'output
    """
    
    @staticmethod
    def enhance_specialist_prompt_for_quality(base_prompt: str, asset_type: Optional[str] = None) -> str:
        """
        Migliora il prompt di uno specialist per evitare fake content e aumentare actionability
        """
        
        try:
            from backend.config.quality_system_config import QualitySystemConfig
        except ImportError:
            logger.warning("QualitySystemConfig not available, using default settings")
            # Valori di fallback
            quality_threshold = 0.8
        else:
            quality_threshold = QualitySystemConfig.QUALITY_SCORE_THRESHOLD
        
        quality_enhancement = f"""

🔧 **ENHANCED QUALITY REQUIREMENTS (AI Quality Assurance Active)**

**CRITICAL: ANTI-THEORETICAL CONTENT POLICY**
- NEVER generate "strategies", "frameworks", or "best practices" without concrete examples
- NEVER use placeholder data like "[Insert content here]", "TBD", "Example post"
- NEVER create generic templates - always fill with REAL, specific content
- NEVER use theoretical language like "should include", "consider adding", "example of"
- REPLACE theoretical concepts with actual implementations

**MANDATORY CONCRETE OUTPUT STANDARDS**
- Every output must contain SPECIFIC, actionable items (dates, times, exact content)
- Provide COMPLETE implementations, not suggestions or guidelines
- Include REAL examples that users can copy/paste immediately
- Generate FULL content lists (if asked for 30 posts, provide 30 complete posts)
- Add SPECIFIC metrics, measurements, and quantified outcomes

**CONCRETE CONTENT CHECKLIST** 
✅ Zero theoretical/strategic language - only concrete deliverables
✅ Complete content ready for immediate business use
✅ Specific examples with real details (dates, names, numbers)
✅ Full implementation details, not just recommendations  
✅ Quantified metrics and measurable outcomes
✅ Business-ready format that requires no additional work

**EXAMPLES OF UNACCEPTABLE THEORETICAL CONTENT**:
❌ "Create engaging posts about fitness topics"
❌ "Develop a content strategy that includes..."
❌ "Consider posting motivational content on Mondays"
❌ "Include relevant hashtags for your audience"

**EXAMPLES OF REQUIRED CONCRETE CONTENT**:
✅ "Post 1 (Dec 20): '💪 5 ESERCIZI MASSA - 1. SQUAT 4x8 reps...' #bodybuilding #palestra"
✅ "Monday 6:00 AM: Morning workout routine video (30 seconds)"
✅ "Caption: 'COLAZIONE PROTEICA 🥚 400 cal: 4 uova + avocado + pane integrale'"

**AI QUALITY ASSESSMENT NOTE**
Your output will be automatically analyzed for:
- Concrete content vs theoretical strategy (Target: 0.9+)
- Immediate actionability without additional work (Target: 0.85+)
- Completeness of all requested deliverables (Target: 0.8+)
- Zero placeholder/template content (Target: 0.9+)

Outputs scoring below {quality_threshold}/1.0 will trigger enhancement tasks. Aim for 0.9+ quality score.

**DOMAIN-SPECIFIC GUIDANCE**:
{DynamicPromptEnhancer._get_domain_specific_guidance(asset_type)}
"""
        
        return base_prompt + quality_enhancement
    
    @staticmethod
    def _get_domain_specific_guidance(asset_type: Optional[str]) -> str:
        """Ottieni guidance specifico per tipo di asset"""
        
        if not asset_type:
            return "Focus on creating business-ready, actionable content with real data."
        
        guidance_map = {
            "contact_database": """
For CONTACT DATABASES:
- Include complete contact information (name, email, phone, company, role)
- Add qualification scores and lead sources
- Provide next action recommendations for each contact
- Include industry and company size data where relevant""",
            
            "content_calendar": """
For CONTENT CALENDARS (CRITICAL - NO THEORETICAL CONTENT):
- Generate COMPLETE posts with full captions, not "post about X topic"
- Include EXACT posting dates and times (e.g., "Monday 18:00")
- Write FULL captions with emojis, hashtags, and CTAs
- Specify DETAILED content ("Carousel: 5 slides showing squat progression")
- Provide ACTUAL hashtag lists (#bodybuilding #palestra #massa)
- Include REAL engagement predictions with numbers""",
            
            "editorial_plan": """
For EDITORIAL PLANS (ANTI-THEORETICAL MODE):
- Generate ACTUAL posts with complete captions, not content ideas
- Provide FULL 30-day calendars with specific posts for each date
- Include REAL captions users can copy-paste immediately
- Write COMPLETE carousel/reel scripts with timing and scenes
- Add SPECIFIC hashtag strategies for each post type
- Include ACTUAL trending audio suggestions and usage tips""",
            
            "training_program": """
For TRAINING PROGRAMS:
- Include specific exercise descriptions with sets/reps/duration
- Provide progression schedules and difficulty adjustments
- Add equipment requirements and alternatives
- Include performance tracking and measurement criteria""",
            
            "financial_model": """
For FINANCIAL MODELS:
- Use realistic financial assumptions and industry benchmarks
- Include detailed revenue and cost breakdowns
- Provide scenario analysis (best/worst/expected case)
- Add cash flow projections and funding requirements""",
            
            "research_database": """
For RESEARCH DATABASES:
- Cite specific, verifiable sources and data points
- Include methodology and data collection approach
- Provide statistical confidence levels where applicable
- Add recommendations based on research findings""",
            
            "strategy_framework": """
For STRATEGY FRAMEWORKS (CONCRETE IMPLEMENTATION FOCUS):
- Provide SPECIFIC KPIs with exact numbers and targets
- Include DETAILED implementation timelines with dates and milestones
- Add REAL resource requirements (tools, budget, team size)
- Include ACTIONABLE competitive analysis with specific actions
- Generate COMPLETE implementation checklists"""
        }
        
        return guidance_map.get(asset_type, "Focus on creating business-ready, actionable content with real data.")
    
    @staticmethod
    def create_quality_focused_task_description(base_description: str, quality_target: float = 0.85) -> str:
        """
        Migliora la descrizione di un task con focus sulla qualità
        """
        
        quality_addendum = f"""

📊 **AI QUALITY TARGET: {quality_target}/1.0 - CONCRETE CONTENT REQUIRED**

This task will be automatically evaluated for quality. Ensure your output meets these standards:
- **Concrete Content**: ZERO theoretical/strategic language, only actionable deliverables (Target: ≥0.9)
- **Completeness**: ALL requested items with FULL details, no placeholders (Target: ≥{quality_target})
- **Immediate Usability**: Ready for copy-paste business use (Target: ≥{quality_target})
- **Specific Examples**: Real dates, numbers, content - no generic templates (Target: ≥0.9)

⚠️ **QUALITY WARNING**: Outputs with theoretical content, placeholders, or incomplete details will automatically trigger enhancement tasks and delay project completion.

✅ **SUCCESS CRITERIA FOR ASSET PRODUCTION**: 
- Zero theoretical/strategic content - only concrete deliverables
- COMPLETE implementation ready for immediate use
- SPECIFIC examples with real data (dates, numbers, names)
- FULL content generation (if 30 posts requested, provide 30 complete posts)
- Business-ready format requiring no additional work"""
        
        return base_description + quality_addendum
    
    @staticmethod
    def enhance_pm_coordination_prompt(base_prompt: str, quality_issues: List[str]) -> str:
        """
        Migliora il prompt per PM quando deve coordinare enhancement di qualità
        """
        
        issues_summary = ", ".join(quality_issues) if quality_issues else "General quality improvements"
        
        pm_enhancement = f"""

🔧 **PROJECT MANAGER: QUALITY COORDINATION MODE**

**SITUATION**: AI Quality Analysis has identified assets requiring improvement.
**YOUR ROLE**: Coordinate enhancement efforts to meet business-ready standards.

**IDENTIFIED ISSUES**: {issues_summary}

**COORDINATION RESPONSIBILITIES**:
1. **Validate AI Findings**: Review quality assessments and confirm priorities
2. **Resource Allocation**: Assign appropriate specialists to enhancement tasks
3. **Quality Standards**: Ensure all enhanced assets meet ≥0.85 quality score (ENHANCED)
4. **Concrete Content Validation**: Verify outputs contain actual implementations, not strategies
5. **Timeline Management**: Balance quality improvement with project deadlines
6. **Final Approval**: Sign off on enhanced assets before client delivery

**QUALITY ESCALATION AUTHORITY**:
- You have final authority to approve/reject AI quality assessments
- You can prioritize critical fixes over minor improvements
- You can request additional specialist resources if needed
- You can approve asset delivery with documented quality exceptions

**SUCCESS METRICS**:
- All critical quality issues resolved
- ≥80% of assets achieve quality score ≥0.8
- Client delivery timeline maintained
- Zero fake/placeholder content in final deliverables"""
        
        return base_prompt + pm_enhancement


class QualityMetricsCollector:
    """
    Collector centralizzato per metriche di qualità - istanza globale
    """
    
    def __init__(self):
        self.quality_assessments: List[Dict[str, Any]] = []
        self.enhancement_activities: List[Dict[str, Any]] = []
        self.system_performance: Dict[str, Any] = {
            "total_assets_analyzed": 0,
            "average_quality_score": 0.0,
            "enhancement_success_rate": 0.0,
            "cost_per_analysis": 0.0,
            "analysis_time_avg": 0.0
        }
    
    def record_quality_assessment(
        self, 
        workspace_id: str, 
        asset_id: str,
        quality_score: float,
        assessment_details: Dict[str, Any]
    ):
        """Registra una valutazione di qualità"""
        
        self.quality_assessments.append({
            "timestamp": datetime.now().isoformat(),
            "workspace_id": workspace_id,
            "asset_id": asset_id,
            "quality_score": quality_score,
            "details": assessment_details
        })
        
        # Aggiorna metriche aggregate
        self._update_aggregate_metrics()
    
    def record_enhancement_activity(
        self,
        workspace_id: str,
        asset_id: str,
        enhancement_type: str,
        success: bool,
        improvement_delta: float = 0.0
    ):
        """Registra un'attività di enhancement"""
        
        self.enhancement_activities.append({
            "timestamp": datetime.now().isoformat(),
            "workspace_id": workspace_id,
            "asset_id": asset_id,
            "enhancement_type": enhancement_type,
            "success": success,
            "improvement_delta": improvement_delta
        })
        
        self._update_aggregate_metrics()
    
    def _update_aggregate_metrics(self):
        """Aggiorna metriche aggregate"""
        
        if self.quality_assessments:
            avg_score = sum(qa["quality_score"] for qa in self.quality_assessments) / len(self.quality_assessments)
            self.system_performance["average_quality_score"] = avg_score
            self.system_performance["total_assets_analyzed"] = len(self.quality_assessments)
        
        if self.enhancement_activities:
            success_rate = sum(1 for ea in self.enhancement_activities if ea["success"]) / len(self.enhancement_activities)
            self.system_performance["enhancement_success_rate"] = success_rate
    
    def get_quality_trends(self, workspace_id: Optional[str] = None) -> Dict[str, Any]:
        """Ottieni trend di qualità"""
        
        assessments = self.quality_assessments
        if workspace_id:
            assessments = [qa for qa in assessments if qa["workspace_id"] == workspace_id]
        
        if not assessments:
            return {"message": "No quality assessments available"}
        
        return {
            "total_assessments": len(assessments),
            "average_quality_score": sum(qa["quality_score"] for qa in assessments) / len(assessments),
            "quality_distribution": {
                "excellent": len([qa for qa in assessments if qa["quality_score"] >= 0.9]),
                "good": len([qa for qa in assessments if 0.8 <= qa["quality_score"] < 0.9]),
                "fair": len([qa for qa in assessments if 0.6 <= qa["quality_score"] < 0.8]),
                "poor": len([qa for qa in assessments if qa["quality_score"] < 0.6])
            },
            "latest_assessment": assessments[-1] if assessments else None,
            "system_performance": self.system_performance
        }
    
    def reset_metrics(self):
        """Reset di tutte le metriche"""
        self.quality_assessments.clear()
        self.enhancement_activities.clear()
        self.system_performance = {
            "total_assets_analyzed": 0,
            "average_quality_score": 0.0,
            "enhancement_success_rate": 0.0,
            "cost_per_analysis": 0.0,
            "analysis_time_avg": 0.0
        }


# Istanza globale per la raccolta metriche
quality_metrics_collector = QualityMetricsCollector()