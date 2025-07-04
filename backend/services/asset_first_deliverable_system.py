"""
Asset-First Concrete Deliverables System

🎯 PILLAR 12: Concrete Deliverables - Asset-first output generation system

Revolutionary approach that prioritizes tangible assets over abstract tasks:
- Real-time asset extraction from task outputs
- AI-driven asset quality validation and enhancement
- Automatic asset categorization and organization
- Business-ready deliverable packaging
- Asset-driven progress measurement
- Concrete value demonstration
"""

import asyncio
import logging
import json
import os
import re
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict

from database import supabase, get_supabase_service_client
from models import TaskStatus

logger = logging.getLogger(__name__)

class AssetType(Enum):
    DOCUMENT = "document"
    SPREADSHEET = "spreadsheet"
    PRESENTATION = "presentation"
    CODE = "code"
    DATA = "data"
    IMAGE = "image"
    VIDEO = "video"
    REPORT = "report"
    PLAN = "plan"
    ANALYSIS = "analysis"
    SPECIFICATION = "specification"
    DESIGN = "design"
    PROTOTYPE = "prototype"

class AssetQuality(Enum):
    DRAFT = "draft"           # Raw output, needs refinement
    WORKING = "working"       # Functional but not polished
    PROFESSIONAL = "professional"  # Business-ready quality
    PREMIUM = "premium"       # Exceptional quality

class DeliverableFormat(Enum):
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    PPTX = "pptx"
    HTML = "html"
    MARKDOWN = "markdown"
    JSON = "json"
    CSV = "csv"

@dataclass
class ConcreteAsset:
    asset_id: str
    asset_type: AssetType
    title: str
    content: str
    quality_level: AssetQuality
    business_value: float  # 0.0 to 1.0
    completeness: float    # 0.0 to 1.0
    metadata: Dict[str, Any]
    source_task_id: Optional[str] = None
    workspace_id: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "asset_type": self.asset_type.value,
            "quality_level": self.quality_level.value,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class AssetFirstDeliverableSystem:
    """
    📦 PILLAR 12: Asset-first deliverable generation system
    
    Revolutionizes project delivery by focusing on concrete, tangible assets
    rather than abstract task completion. Automatically extracts, validates,
    and packages business-ready deliverables from work outputs.
    """
    
    def __init__(self):
        self.supabase_service = get_supabase_service_client()
        self.asset_extractors = self._initialize_asset_extractors()
        self.quality_enhancers = self._initialize_quality_enhancers()
        self.packaging_templates = self._initialize_packaging_templates()
        
    def _initialize_asset_extractors(self) -> Dict[str, Dict[str, Any]]:
        """Initialize AI-powered asset extraction patterns"""
        return {
            "document_patterns": {
                "report": r"(.*(?:report|analysis|summary|findings).*)",
                "plan": r"(.*(?:plan|strategy|roadmap|timeline).*)",
                "specification": r"(.*(?:spec|requirements|criteria).*)",
                "guide": r"(.*(?:guide|manual|instructions|tutorial).*)"
            },
            "data_patterns": {
                "metrics": r"(\d+(?:\.\d+)?%?)\s*(?:increase|decrease|improvement|growth|decline)",
                "statistics": r"(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:users|customers|revenue|sales)",
                "kpis": r"(?:kpi|metric|indicator).*?(\d+(?:\.\d+)?)",
                "trends": r"((?:up|down|increasing|decreasing|trending).*?(?:\d+%?))"
            },
            "business_content": {
                "recommendations": r"(?:recommend|suggest|propose).*?([A-Z][^.]*\.)",
                "insights": r"(?:insight|finding|discovery).*?([A-Z][^.]*\.)",
                "action_items": r"(?:action|next step|todo).*?([A-Z][^.]*\.)",
                "conclusions": r"(?:conclusion|summary|result).*?([A-Z][^.]*\.)"
            },
            "technical_content": {
                "code_blocks": r"```(?:\w+)?\n(.*?)\n```",
                "configurations": r"(?:config|settings|parameters).*?({.*?})",
                "apis": r"(?:api|endpoint).*?(https?://[^\s]+)",
                "schemas": r"(?:schema|structure|format).*?({.*?})"
            }
        }
    
    def _initialize_quality_enhancers(self) -> Dict[str, Dict[str, Any]]:
        """Initialize AI quality enhancement strategies"""
        return {
            "document_enhancement": {
                "structure_improvement": "Add executive summary, clear sections, professional formatting",
                "content_enrichment": "Expand key points, add context, improve clarity",
                "business_focus": "Emphasize business value, ROI, strategic impact",
                "actionability": "Convert insights into specific action items"
            },
            "data_enhancement": {
                "visualization_ready": "Format data for charts and graphs",
                "trend_analysis": "Add trend interpretation and projections",
                "benchmarking": "Include industry benchmarks and comparisons",
                "executive_summary": "Create high-level data story for executives"
            },
            "presentation_enhancement": {
                "slide_structure": "Organize content into presentation-ready slides",
                "visual_elements": "Add placeholder for charts, diagrams, images",
                "narrative_flow": "Create compelling story arc",
                "call_to_action": "End with clear next steps or decisions needed"
            }
        }
    
    def _initialize_packaging_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize deliverable packaging templates"""
        return {
            "business_report": {
                "sections": ["Executive Summary", "Analysis", "Findings", "Recommendations", "Next Steps"],
                "format": DeliverableFormat.PDF,
                "quality_threshold": 0.8,
                "required_assets": ["analysis", "data", "recommendations"]
            },
            "project_plan": {
                "sections": ["Overview", "Objectives", "Timeline", "Resources", "Risks", "Success Metrics"],
                "format": DeliverableFormat.DOCX,
                "quality_threshold": 0.7,
                "required_assets": ["plan", "timeline", "resources"]
            },
            "technical_specification": {
                "sections": ["Requirements", "Architecture", "Implementation", "Testing", "Deployment"],
                "format": DeliverableFormat.MARKDOWN,
                "quality_threshold": 0.8,
                "required_assets": ["specification", "code", "configuration"]
            },
            "market_analysis": {
                "sections": ["Market Overview", "Competitive Analysis", "Trends", "Opportunities", "Strategy"],
                "format": DeliverableFormat.PDF,
                "quality_threshold": 0.8,
                "required_assets": ["analysis", "data", "insights"]
            },
            "presentation_deck": {
                "sections": ["Title", "Agenda", "Key Points", "Data/Charts", "Conclusions", "Next Steps"],
                "format": DeliverableFormat.PPTX,
                "quality_threshold": 0.7,
                "required_assets": ["presentation", "data", "insights"]
            }
        }
    
    async def extract_assets_from_task_output(
        self, 
        task_id: str, 
        task_output: str, 
        task_metadata: Dict[str, Any]
    ) -> List[ConcreteAsset]:
        """
        Extract concrete assets from task output using AI and pattern matching
        
        Args:
            task_id: Source task identifier
            task_output: Raw task output content
            task_metadata: Task context and metadata
            
        Returns:
            List of extracted concrete assets
        """
        extraction_start = datetime.now()
        extracted_assets = []
        
        try:
            logger.info(f"📦 Extracting assets from task {task_id}")
            
            # Step 1: AI-powered asset identification
            asset_candidates = await self._identify_assets_with_ai(task_output, task_metadata)
            
            # Step 2: Pattern-based asset extraction
            pattern_assets = await self._extract_assets_with_patterns(task_output, task_metadata)
            
            # Step 3: Merge and deduplicate assets
            all_assets = asset_candidates + pattern_assets
            deduplicated_assets = self._deduplicate_assets(all_assets)
            
            # Step 4: Quality assessment and enhancement
            for asset_data in deduplicated_assets:
                enhanced_asset = await self._assess_and_enhance_asset(asset_data, task_metadata)
                
                if enhanced_asset and enhanced_asset.quality_level != AssetQuality.DRAFT:
                    # Create ConcreteAsset instance
                    concrete_asset = ConcreteAsset(
                        asset_id=f"asset_{task_id}_{len(extracted_assets)}",
                        asset_type=enhanced_asset.asset_type,
                        title=enhanced_asset.title,
                        content=enhanced_asset.content,
                        quality_level=enhanced_asset.quality_level,
                        business_value=enhanced_asset.business_value,
                        completeness=enhanced_asset.completeness,
                        metadata=enhanced_asset.metadata,
                        source_task_id=task_id,
                        workspace_id=task_metadata.get("workspace_id"),
                        created_at=datetime.now()
                    )
                    
                    # Store asset in database
                    await self._store_asset(concrete_asset)
                    extracted_assets.append(concrete_asset)
            
            extraction_time = (datetime.now() - extraction_start).total_seconds()
            logger.info(f"✅ Extracted {len(extracted_assets)} assets from task {task_id} in {extraction_time:.1f}s")
            
            return extracted_assets
            
        except Exception as e:
            logger.error(f"Error extracting assets from task {task_id}: {e}")
            return []
    
    async def _identify_assets_with_ai(
        self, 
        content: str, 
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Use AI to identify potential assets in content"""
        try:
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                return []
            
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=openai_api_key)
            
            prompt = f"""Analyze this task output and identify concrete, tangible assets that could be valuable business deliverables.

TASK OUTPUT:
{content[:3000]}  # Limit to first 3000 chars

CONTEXT:
- Task Type: {metadata.get('task_type', 'general')}
- Goal: {metadata.get('goal_description', 'Not specified')}
- Domain: {metadata.get('domain', 'business')}

Identify assets in JSON format:
{{
    "assets": [
        {{
            "asset_type": "document|spreadsheet|presentation|report|plan|analysis|specification|data|code",
            "title": "Clear, professional title for the asset",
            "content_excerpt": "Key content that makes this asset valuable (max 500 chars)",
            "business_value": 0.0-1.0,
            "completeness": 0.0-1.0,
            "quality_indicators": ["indicator1", "indicator2"],
            "asset_category": "primary|supporting|reference",
            "deliverable_potential": "high|medium|low",
            "enhancement_needs": ["need1", "need2"]
        }}
    ]
}}

Focus on:
1. Concrete, tangible outputs (not abstract concepts)
2. Business value and practical utility
3. Professional presentation potential
4. Completeness and actionability
5. Unique insights or recommendations

Only identify assets that have real business value and substance."""

            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert business analyst who identifies valuable, concrete assets from work outputs."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get("assets", [])
            
        except Exception as e:
            logger.warning(f"AI asset identification failed: {e}")
            return []
    
    async def _extract_assets_with_patterns(
        self, 
        content: str, 
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract assets using pattern matching"""
        pattern_assets = []
        
        try:
            # Extract document-type assets
            for doc_type, pattern in self.asset_extractors["document_patterns"].items():
                matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    if len(match.strip()) > 50:  # Minimum content length
                        pattern_assets.append({
                            "asset_type": "document",
                            "title": f"{doc_type.title()}: {match[:50]}...",
                            "content_excerpt": match[:500],
                            "business_value": 0.6,
                            "completeness": 0.7,
                            "asset_category": "primary",
                            "extraction_method": "pattern_matching"
                        })
            
            # Extract data assets
            data_points = []
            for data_type, pattern in self.asset_extractors["data_patterns"].items():
                matches = re.findall(pattern, content, re.IGNORECASE)
                data_points.extend([(data_type, match) for match in matches])
            
            if len(data_points) >= 3:  # Need multiple data points for valuable asset
                data_content = "\n".join([f"{dtype}: {value}" for dtype, value in data_points])
                pattern_assets.append({
                    "asset_type": "data",
                    "title": "Key Metrics and Data Points",
                    "content_excerpt": data_content[:500],
                    "business_value": 0.8,
                    "completeness": 0.8,
                    "asset_category": "primary",
                    "extraction_method": "pattern_matching"
                })
            
            # Extract business insights
            insights = []
            for insight_type, pattern in self.asset_extractors["business_content"].items():
                matches = re.findall(pattern, content, re.IGNORECASE)
                insights.extend([(insight_type, match) for match in matches])
            
            if len(insights) >= 2:
                insights_content = "\n".join([f"{itype}: {text}" for itype, text in insights])
                pattern_assets.append({
                    "asset_type": "analysis",
                    "title": "Business Insights and Recommendations",
                    "content_excerpt": insights_content[:500],
                    "business_value": 0.9,
                    "completeness": 0.7,
                    "asset_category": "primary",
                    "extraction_method": "pattern_matching"
                })
            
            return pattern_assets
            
        except Exception as e:
            logger.error(f"Error in pattern-based asset extraction: {e}")
            return []
    
    def _deduplicate_assets(self, assets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate or highly similar assets"""
        if not assets:
            return []
        
        deduplicated = []
        
        for asset in assets:
            is_duplicate = False
            asset_content = asset.get("content_excerpt", "").lower()
            
            for existing in deduplicated:
                existing_content = existing.get("content_excerpt", "").lower()
                
                # Simple similarity check based on content overlap
                if asset_content and existing_content:
                    # Check for substantial overlap
                    common_words = set(asset_content.split()) & set(existing_content.split())
                    total_words = max(len(asset_content.split()), len(existing_content.split()))
                    
                    if len(common_words) / max(total_words, 1) > 0.7:  # 70% similarity threshold
                        is_duplicate = True
                        # Keep the higher quality asset
                        if asset.get("business_value", 0) > existing.get("business_value", 0):
                            deduplicated.remove(existing)
                            deduplicated.append(asset)
                        break
            
            if not is_duplicate:
                deduplicated.append(asset)
        
        return deduplicated
    
    async def _assess_and_enhance_asset(
        self, 
        asset_data: Dict[str, Any], 
        task_metadata: Dict[str, Any]
    ) -> Optional[ConcreteAsset]:
        """Assess asset quality and enhance if needed"""
        try:
            # Basic quality assessment
            content = asset_data.get("content_excerpt", "")
            business_value = asset_data.get("business_value", 0.5)
            completeness = asset_data.get("completeness", 0.5)
            
            # Determine quality level
            quality_score = (business_value + completeness) / 2
            
            if quality_score >= 0.8:
                quality_level = AssetQuality.PROFESSIONAL
            elif quality_score >= 0.6:
                quality_level = AssetQuality.WORKING
            else:
                quality_level = AssetQuality.DRAFT
            
            # Skip low-quality drafts
            if quality_level == AssetQuality.DRAFT and quality_score < 0.4:
                return None
            
            # AI enhancement for working+ quality assets
            if quality_level in [AssetQuality.WORKING, AssetQuality.PROFESSIONAL]:
                enhanced_content = await self._enhance_asset_with_ai(asset_data, task_metadata)
                if enhanced_content:
                    content = enhanced_content
                    # Boost quality after enhancement
                    if quality_level == AssetQuality.WORKING:
                        quality_level = AssetQuality.PROFESSIONAL
            
            # Create enhanced asset
            asset_type = AssetType(asset_data.get("asset_type", "document"))
            
            enhanced_asset = ConcreteAsset(
                asset_id="",  # Will be set by caller
                asset_type=asset_type,
                title=asset_data.get("title", "Untitled Asset"),
                content=content,
                quality_level=quality_level,
                business_value=business_value,
                completeness=completeness,
                metadata={
                    "extraction_method": asset_data.get("extraction_method", "ai"),
                    "enhancement_applied": quality_level != AssetQuality.DRAFT,
                    "asset_category": asset_data.get("asset_category", "primary"),
                    "quality_indicators": asset_data.get("quality_indicators", []),
                    "deliverable_potential": asset_data.get("deliverable_potential", "medium")
                }
            )
            
            return enhanced_asset
            
        except Exception as e:
            logger.error(f"Error assessing/enhancing asset: {e}")
            return None
    
    async def _enhance_asset_with_ai(
        self, 
        asset_data: Dict[str, Any], 
        task_metadata: Dict[str, Any]
    ) -> Optional[str]:
        """Use AI to enhance asset quality and presentation"""
        try:
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                return None
            
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=openai_api_key)
            
            asset_type = asset_data.get("asset_type", "document")
            content = asset_data.get("content_excerpt", "")
            
            enhancement_strategy = self.quality_enhancers.get(f"{asset_type}_enhancement", {})
            
            prompt = f"""Enhance this {asset_type} asset to professional business quality:

CURRENT CONTENT:
{content}

ASSET CONTEXT:
- Type: {asset_type}
- Business Value: {asset_data.get('business_value', 'Unknown')}
- Target Audience: Business stakeholders
- Purpose: {task_metadata.get('goal_description', 'Business deliverable')}

ENHANCEMENT REQUIREMENTS:
{enhancement_strategy.get('structure_improvement', 'Improve structure and clarity')}
{enhancement_strategy.get('content_enrichment', 'Enrich content quality')}
{enhancement_strategy.get('business_focus', 'Emphasize business value')}

Please enhance the content to be:
1. Professional and business-ready
2. Well-structured and organized
3. Clear and actionable
4. Focused on business value
5. Suitable for executive presentation

Return only the enhanced content, formatted professionally."""

            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert business writer who creates professional, high-quality business documents."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1500
            )
            
            enhanced_content = response.choices[0].message.content.strip()
            
            # Validate enhancement (must be substantially longer and higher quality)
            if len(enhanced_content) > len(content) * 1.2:  # At least 20% longer
                return enhanced_content
            
            return None
            
        except Exception as e:
            logger.warning(f"AI asset enhancement failed: {e}")
            return None
    
    async def _store_asset(self, asset: ConcreteAsset):
        """Store asset in database"""
        try:
            asset_data = {
                "asset_id": asset.asset_id,
                "workspace_id": asset.workspace_id,
                "source_task_id": asset.source_task_id,
                "asset_type": asset.asset_type.value,
                "title": asset.title,
                "content": asset.content,
                "quality_level": asset.quality_level.value,
                "business_value": asset.business_value,
                "completeness": asset.completeness,
                "metadata": asset.metadata,
                "created_at": asset.created_at.isoformat() if asset.created_at else datetime.now().isoformat()
            }
            
            # Store in workspace_assets table (create if doesn't exist)
            result = supabase.table("workspace_assets").insert(asset_data).execute()
            
            if result.data:
                logger.debug(f"✅ Stored asset {asset.asset_id}: {asset.title}")
            else:
                logger.warning(f"Failed to store asset {asset.asset_id}")
                
        except Exception as e:
            logger.error(f"Error storing asset {asset.asset_id}: {e}")
    
    async def generate_deliverable_package(
        self, 
        workspace_id: str, 
        deliverable_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a complete deliverable package from workspace assets
        
        Args:
            workspace_id: Target workspace
            deliverable_type: Specific deliverable type to generate (auto-detect if None)
            
        Returns:
            Packaged deliverable with formatted content
        """
        try:
            logger.info(f"📦 Generating deliverable package for workspace {workspace_id}")
            
            # Step 1: Get all assets for workspace
            assets_response = supabase.table("workspace_assets").select("*").eq(
                "workspace_id", workspace_id
            ).execute()
            
            assets_data = assets_response.data or []
            
            if not assets_data:
                return {
                    "success": False,
                    "error": "No assets found in workspace",
                    "workspace_id": workspace_id
                }
            
            # Convert to ConcreteAsset objects
            assets = []
            for asset_data in assets_data:
                asset = ConcreteAsset(
                    asset_id=asset_data["asset_id"],
                    asset_type=AssetType(asset_data["asset_type"]),
                    title=asset_data["title"],
                    content=asset_data["content"],
                    quality_level=AssetQuality(asset_data["quality_level"]),
                    business_value=asset_data["business_value"],
                    completeness=asset_data["completeness"],
                    metadata=asset_data.get("metadata", {}),
                    workspace_id=asset_data["workspace_id"],
                    source_task_id=asset_data.get("source_task_id"),
                    created_at=datetime.fromisoformat(asset_data["created_at"])
                )
                assets.append(asset)
            
            # Step 2: Determine optimal deliverable type
            if not deliverable_type:
                deliverable_type = await self._determine_optimal_deliverable_type(assets)
            
            # Step 3: Generate deliverable package
            deliverable_package = await self._create_deliverable_package(
                workspace_id, deliverable_type, assets
            )
            
            # Step 4: Store deliverable in database
            if deliverable_package["success"]:
                await self._store_deliverable_package(deliverable_package)
            
            return deliverable_package
            
        except Exception as e:
            logger.error(f"Error generating deliverable package: {e}")
            return {
                "success": False,
                "error": str(e),
                "workspace_id": workspace_id
            }
    
    async def _determine_optimal_deliverable_type(self, assets: List[ConcreteAsset]) -> str:
        """Determine the best deliverable type based on available assets"""
        try:
            # Analyze asset composition
            asset_types = [asset.asset_type for asset in assets]
            asset_type_counts = {asset_type: asset_types.count(asset_type) for asset_type in set(asset_types)}
            
            # Quality and value analysis
            high_quality_assets = [a for a in assets if a.quality_level in [AssetQuality.PROFESSIONAL, AssetQuality.PREMIUM]]
            high_value_assets = [a for a in assets if a.business_value >= 0.7]
            
            # Rule-based determination
            if AssetType.ANALYSIS in asset_type_counts and AssetType.DATA in asset_type_counts:
                return "market_analysis"
            elif AssetType.PLAN in asset_type_counts:
                return "project_plan"
            elif AssetType.SPECIFICATION in asset_type_counts or AssetType.CODE in asset_type_counts:
                return "technical_specification"
            elif len(high_value_assets) >= 3 and any(a.asset_type == AssetType.REPORT for a in assets):
                return "business_report"
            elif any("presentation" in a.metadata.get("deliverable_potential", "") for a in assets):
                return "presentation_deck"
            else:
                return "business_report"  # Default fallback
                
        except Exception as e:
            logger.warning(f"Error determining deliverable type, using default: {e}")
            return "business_report"
    
    async def _create_deliverable_package(
        self, 
        workspace_id: str, 
        deliverable_type: str, 
        assets: List[ConcreteAsset]
    ) -> Dict[str, Any]:
        """Create formatted deliverable package"""
        try:
            template = self.packaging_templates.get(deliverable_type, self.packaging_templates["business_report"])
            
            # Filter assets by quality threshold
            quality_threshold = template["quality_threshold"]
            qualified_assets = [
                a for a in assets 
                if a.business_value >= quality_threshold and a.quality_level != AssetQuality.DRAFT
            ]
            
            if len(qualified_assets) < len(template["required_assets"]):
                return {
                    "success": False,
                    "error": f"Insufficient quality assets for {deliverable_type}",
                    "required": len(template["required_assets"]),
                    "available": len(qualified_assets)
                }
            
            # Generate formatted content
            formatted_content = await self._format_deliverable_content(
                deliverable_type, template, qualified_assets
            )
            
            # Create deliverable package
            package = {
                "success": True,
                "workspace_id": workspace_id,
                "deliverable_type": deliverable_type,
                "title": f"{deliverable_type.replace('_', ' ').title()} - {datetime.now().strftime('%Y-%m-%d')}",
                "format": template["format"].value,
                "content": formatted_content,
                "assets_included": len(qualified_assets),
                "total_assets": len(assets),
                "quality_score": sum(a.business_value for a in qualified_assets) / len(qualified_assets),
                "completeness": sum(a.completeness for a in qualified_assets) / len(qualified_assets),
                "created_at": datetime.now().isoformat(),
                "metadata": {
                    "template_used": deliverable_type,
                    "sections": template["sections"],
                    "asset_breakdown": {
                        asset_type.value: len([a for a in qualified_assets if a.asset_type == asset_type])
                        for asset_type in AssetType
                    },
                    "quality_distribution": {
                        quality.value: len([a for a in qualified_assets if a.quality_level == quality])
                        for quality in AssetQuality
                    }
                }
            }
            
            return package
            
        except Exception as e:
            logger.error(f"Error creating deliverable package: {e}")
            return {
                "success": False,
                "error": str(e),
                "workspace_id": workspace_id
            }
    
    async def _format_deliverable_content(
        self, 
        deliverable_type: str, 
        template: Dict[str, Any], 
        assets: List[ConcreteAsset]
    ) -> str:
        """Format assets into professional deliverable content"""
        try:
            sections = template["sections"]
            formatted_sections = []
            
            # Create title section
            title = f"{deliverable_type.replace('_', ' ').title()}"
            formatted_sections.append(f"# {title}")
            formatted_sections.append(f"*Generated on {datetime.now().strftime('%B %d, %Y')}*\n")
            
            # Organize assets by section
            asset_mapping = self._map_assets_to_sections(sections, assets)
            
            for section in sections:
                formatted_sections.append(f"## {section}")
                
                section_assets = asset_mapping.get(section, [])
                
                if section_assets:
                    for asset in section_assets:
                        formatted_sections.append(f"### {asset.title}")
                        formatted_sections.append(asset.content)
                        formatted_sections.append("")  # Empty line
                else:
                    # Generate placeholder content for missing sections
                    placeholder = f"*{section} content will be added based on additional project outputs.*"
                    formatted_sections.append(placeholder)
                
                formatted_sections.append("")  # Section separator
            
            # Add metadata footer
            formatted_sections.append("---")
            formatted_sections.append("## Document Information")
            formatted_sections.append(f"- **Assets Included**: {len(assets)}")
            formatted_sections.append(f"- **Quality Score**: {sum(a.business_value for a in assets) / len(assets):.1%}")
            formatted_sections.append(f"- **Completeness**: {sum(a.completeness for a in assets) / len(assets):.1%}")
            formatted_sections.append(f"- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
            
            return "\n".join(formatted_sections)
            
        except Exception as e:
            logger.error(f"Error formatting deliverable content: {e}")
            return f"# {deliverable_type.replace('_', ' ').title()}\n\nError formatting content: {str(e)}"
    
    def _map_assets_to_sections(
        self, 
        sections: List[str], 
        assets: List[ConcreteAsset]
    ) -> Dict[str, List[ConcreteAsset]]:
        """Map assets to appropriate sections based on content and type"""
        section_mapping = {}
        
        # Keywords for section matching
        section_keywords = {
            "Executive Summary": ["summary", "overview", "key", "main"],
            "Analysis": ["analysis", "finding", "result", "data"],
            "Findings": ["finding", "discovery", "insight", "result"],
            "Recommendations": ["recommend", "suggest", "action", "next"],
            "Next Steps": ["next", "action", "step", "follow"],
            "Overview": ["overview", "introduction", "background"],
            "Objectives": ["objective", "goal", "target", "aim"],
            "Timeline": ["timeline", "schedule", "plan", "phase"],
            "Resources": ["resource", "requirement", "need", "capacity"],
            "Risks": ["risk", "challenge", "issue", "concern"],
            "Success Metrics": ["metric", "kpi", "measure", "success"],
            "Requirements": ["requirement", "specification", "criteria"],
            "Architecture": ["architecture", "design", "structure"],
            "Implementation": ["implementation", "development", "build"],
            "Testing": ["test", "validation", "verification"],
            "Deployment": ["deployment", "release", "launch"],
            "Market Overview": ["market", "industry", "sector"],
            "Competitive Analysis": ["competitive", "competitor", "comparison"],
            "Trends": ["trend", "pattern", "direction"],
            "Opportunities": ["opportunity", "potential", "possibility"],
            "Strategy": ["strategy", "approach", "plan"]
        }
        
        # Initialize all sections
        for section in sections:
            section_mapping[section] = []
        
        # Map assets to sections
        for asset in assets:
            best_section = None
            best_score = 0
            
            asset_text = (asset.title + " " + asset.content).lower()
            
            for section in sections:
                keywords = section_keywords.get(section, [])
                score = sum(1 for keyword in keywords if keyword in asset_text)
                
                # Boost score for asset type alignment
                if section == "Analysis" and asset.asset_type in [AssetType.ANALYSIS, AssetType.DATA]:
                    score += 2
                elif section == "Requirements" and asset.asset_type == AssetType.SPECIFICATION:
                    score += 2
                elif section in ["Timeline", "Next Steps"] and asset.asset_type == AssetType.PLAN:
                    score += 2
                
                if score > best_score:
                    best_score = score
                    best_section = section
            
            # Assign to best matching section, or first section if no good match
            target_section = best_section if best_score > 0 else sections[0]
            section_mapping[target_section].append(asset)
        
        return section_mapping
    
    async def _store_deliverable_package(self, package: Dict[str, Any]):
        """Store deliverable package in database"""
        try:
            deliverable_data = {
                "workspace_id": package["workspace_id"],
                "name": package["title"],
                "description": f"Auto-generated {package['deliverable_type']} from workspace assets",
                "deliverable_type": package["deliverable_type"],
                "status": "completed",
                "content": {
                    "formatted_content": package["content"],
                    "format": package["format"],
                    "quality_score": package["quality_score"],
                    "completeness": package["completeness"],
                    "assets_included": package["assets_included"],
                    "metadata": package["metadata"]
                },
                "created_at": package["created_at"]
            }
            
            result = supabase.table("workspace_deliverables").insert(deliverable_data).execute()
            
            if result.data:
                logger.info(f"✅ Stored deliverable package: {package['title']}")
            else:
                logger.warning(f"Failed to store deliverable package")
                
        except Exception as e:
            logger.error(f"Error storing deliverable package: {e}")
    
    async def get_workspace_asset_summary(self, workspace_id: str) -> Dict[str, Any]:
        """Get comprehensive summary of workspace assets"""
        try:
            # Get all assets
            assets_response = supabase.table("workspace_assets").select("*").eq(
                "workspace_id", workspace_id
            ).execute()
            
            assets_data = assets_response.data or []
            
            if not assets_data:
                return {
                    "workspace_id": workspace_id,
                    "total_assets": 0,
                    "asset_summary": "No assets found"
                }
            
            # Analyze assets
            asset_types = [a["asset_type"] for a in assets_data]
            quality_levels = [a["quality_level"] for a in assets_data]
            business_values = [a["business_value"] for a in assets_data]
            
            # Calculate statistics
            summary = {
                "workspace_id": workspace_id,
                "total_assets": len(assets_data),
                "asset_breakdown": {
                    asset_type.value: asset_types.count(asset_type.value)
                    for asset_type in AssetType
                    if asset_types.count(asset_type.value) > 0
                },
                "quality_distribution": {
                    quality.value: quality_levels.count(quality.value)
                    for quality in AssetQuality
                    if quality_levels.count(quality.value) > 0
                },
                "average_business_value": sum(business_values) / len(business_values),
                "high_value_assets": len([v for v in business_values if v >= 0.8]),
                "professional_quality_assets": quality_levels.count("professional") + quality_levels.count("premium"),
                "deliverable_readiness": {
                    "business_report": self._assess_deliverable_readiness("business_report", assets_data),
                    "project_plan": self._assess_deliverable_readiness("project_plan", assets_data),
                    "technical_specification": self._assess_deliverable_readiness("technical_specification", assets_data),
                    "market_analysis": self._assess_deliverable_readiness("market_analysis", assets_data),
                    "presentation_deck": self._assess_deliverable_readiness("presentation_deck", assets_data)
                },
                "recommendations": self._generate_asset_recommendations(assets_data)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating asset summary: {e}")
            return {
                "workspace_id": workspace_id,
                "error": str(e)
            }
    
    def _assess_deliverable_readiness(self, deliverable_type: str, assets_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess readiness for a specific deliverable type"""
        template = self.packaging_templates.get(deliverable_type, {})
        quality_threshold = template.get("quality_threshold", 0.7)
        required_assets = template.get("required_assets", [])
        
        # Filter qualified assets
        qualified_assets = [
            a for a in assets_data
            if a["business_value"] >= quality_threshold and a["quality_level"] != "draft"
        ]
        
        readiness_score = min(len(qualified_assets) / max(len(required_assets), 1), 1.0)
        
        return {
            "readiness_score": readiness_score,
            "ready": readiness_score >= 0.8,
            "qualified_assets": len(qualified_assets),
            "required_assets": len(required_assets),
            "quality_threshold": quality_threshold
        }
    
    def _generate_asset_recommendations(self, assets_data: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations for improving asset portfolio"""
        recommendations = []
        
        if not assets_data:
            recommendations.append("No assets found - focus on task execution to generate concrete outputs")
            return recommendations
        
        # Quality analysis
        draft_count = len([a for a in assets_data if a["quality_level"] == "draft"])
        total_assets = len(assets_data)
        
        if draft_count / total_assets > 0.5:
            recommendations.append("High number of draft-quality assets - focus on enhancement and refinement")
        
        # Business value analysis
        low_value_assets = len([a for a in assets_data if a["business_value"] < 0.5])
        
        if low_value_assets > 0:
            recommendations.append(f"{low_value_assets} assets have low business value - consider enhancement or removal")
        
        # Asset type diversity
        asset_types = set(a["asset_type"] for a in assets_data)
        
        if len(asset_types) < 3:
            recommendations.append("Limited asset type diversity - consider generating different types of outputs")
        
        # Deliverable readiness
        professional_assets = len([a for a in assets_data if a["quality_level"] in ["professional", "premium"]])
        
        if professional_assets >= 3:
            recommendations.append("Sufficient professional assets available - ready for deliverable generation")
        elif professional_assets >= 1:
            recommendations.append("Some professional assets available - consider enhancing remaining assets")
        else:
            recommendations.append("No professional-quality assets - focus on quality improvement")
        
        return recommendations

# Singleton instance
asset_first_deliverable_system = AssetFirstDeliverableSystem()