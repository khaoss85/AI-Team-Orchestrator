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

**CRITICAL: ZERO FAKE CONTENT POLICY**
- NEVER use placeholder data like "John Doe", "Jane Smith", "example.com", "555-1234"
- NEVER generate fake emails, phone numbers, or addresses  
- NEVER use "Lorem ipsum" or template text
- NEVER use generic company names like "ABC Corp", "XYZ Inc"
- If you lack specific data, state "Research needed for [specific data point]"

**ACTIONABILITY STANDARDS**
- Every output must be immediately implementable by the client
- Provide specific, concrete data derived from actual research or analysis
- Include real business metrics, authentic contact information, actual market data
- Replace ALL generic examples with domain-specific, actionable content
- Include specific implementation steps and success criteria

**QUALITY VALIDATION CHECKLIST**
✅ All data points are specific and realistic
✅ No placeholder or example content present  
✅ Asset follows domain best practices for {asset_type or 'business assets'}
✅ Ready for immediate business implementation
✅ Includes concrete next steps and success criteria
✅ Contains measurable outcomes and KPIs

**AI QUALITY ASSESSMENT NOTE**
Your output will be automatically analyzed for:
- Content authenticity (fake content detection)
- Actionability level (immediate usability)  
- Completeness (missing information detection)
- Professional readiness (business standard compliance)

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
For CONTENT CALENDARS:
- Specify exact posting dates and times
- Include complete captions and hashtag strategies  
- Provide content type specifications (image, video, carousel)
- Add engagement predictions and performance metrics""",
            
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
For STRATEGY FRAMEWORKS:
- Include specific KPIs and success metrics
- Provide implementation timelines and resource requirements
- Add risk assessments and mitigation strategies
- Include competitive analysis and market positioning"""
        }
        
        return guidance_map.get(asset_type, "Focus on creating business-ready, actionable content with real data.")
    
    @staticmethod
    def create_quality_focused_task_description(base_description: str, quality_target: float = 0.8) -> str:
        """
        Migliora la descrizione di un task con focus sulla qualità
        """
        
        quality_addendum = f"""

📊 **AI QUALITY TARGET: {quality_target}/1.0**

This task will be automatically evaluated for quality. Ensure your output meets these standards:
- **Authenticity**: Real data, no fake/placeholder content (Target: ≥{quality_target})
- **Actionability**: Immediately usable for business purposes (Target: ≥{quality_target})
- **Completeness**: All necessary information included (Target: ≥{quality_target})
- **Professional**: Business-ready format and presentation

⚠️ **QUALITY WARNING**: Outputs scoring below {quality_target} will automatically trigger enhancement tasks and may delay project completion.

✅ **SUCCESS CRITERIA**: 
- Zero fake/placeholder content
- Immediately actionable by client
- Complete and professional presentation
- Specific implementation guidance included"""
        
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
3. **Quality Standards**: Ensure all enhanced assets meet ≥0.8 quality score
4. **Timeline Management**: Balance quality improvement with project deadlines
5. **Final Approval**: Sign off on enhanced assets before client delivery

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