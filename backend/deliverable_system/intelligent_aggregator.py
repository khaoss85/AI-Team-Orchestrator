"""
Intelligent Deliverable Aggregator - AI-Powered Asset Aggregation
Intelligently combines extracted assets into coherent, valuable deliverables
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import asyncio

from services.ai_provider_abstraction import ai_provider_manager

logger = logging.getLogger(__name__)

class IntelligentDeliverableAggregator:
    """
    Intelligently aggregates assets into meaningful deliverables.
    Implements Pillar 5: Goal-Driven System (deliverables aligned with goals)
    Implements Pillar 12: Concrete Deliverables (real value, no placeholders)
    """
    
    def __init__(self):
        self.aggregation_strategies = {
            'code': self._aggregate_code_assets,
            'documentation': self._aggregate_documentation_assets,
            'data': self._aggregate_data_assets,
            'mixed': self._aggregate_mixed_assets
        }
    
    async def aggregate_assets_to_deliverable(
        self, 
        assets: List[Dict[str, Any]], 
        context: Dict[str, Any],
        goal_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main method to aggregate assets into a coherent deliverable.
        
        Args:
            assets: List of extracted assets with metadata
            context: Information about workspace, project, domain
            goal_info: Optional goal information for alignment
            
        Returns:
            Structured deliverable with aggregated content
        """
        try:
            logger.info(f"🔄 Starting intelligent aggregation of {len(assets)} assets")
            
            if not assets:
                return self._create_empty_deliverable("No assets to aggregate")
            
            # Step 1: Classify assets and determine strategy
            asset_classification = self._classify_assets(assets)
            strategy = self._determine_aggregation_strategy(asset_classification)
            
            # Step 2: AI-powered content organization
            organized_structure = await self._ai_organize_content(assets, context, goal_info)
            
            # Step 3: Apply aggregation strategy
            aggregated_content = await self.aggregation_strategies[strategy](
                assets, organized_structure, context
            )
            
            # Step 4: Generate executive summary
            executive_summary = await self._generate_executive_summary(
                aggregated_content, assets, context, goal_info
            )
            
            # Step 5: Create final deliverable structure
            deliverable = self._create_deliverable_structure(
                executive_summary,
                aggregated_content,
                assets,
                context,
                strategy
            )
            
            # Step 6: Quality score and metadata
            deliverable['quality_metrics'] = self._calculate_deliverable_quality(deliverable, assets)
            deliverable['metadata'] = self._generate_metadata(assets, context, strategy)
            
            logger.info(f"✅ Created deliverable with quality score: {deliverable['quality_metrics']['overall_score']:.2f}")
            return deliverable
            
        except Exception as e:
            logger.error(f"Aggregation failed: {e}")
            return self._create_error_deliverable(str(e), assets)
    
    def _classify_assets(self, assets: List[Dict[str, Any]]) -> Dict[str, int]:
        """Classify assets by type"""
        classification = {
            'code': 0,
            'data': 0,
            'documents': 0,
            'references': 0,
            'other': 0
        }
        
        for asset in assets:
            asset_type = asset.get('asset_type', 'other')
            if asset_type in classification:
                classification[asset_type] += 1
            else:
                classification['other'] += 1
        
        return classification
    
    def _determine_aggregation_strategy(self, classification: Dict[str, int]) -> str:
        """Determine best aggregation strategy based on asset types"""
        total = sum(classification.values())
        if total == 0:
            return 'mixed'
        
        # Calculate percentages
        code_pct = classification['code'] / total
        doc_pct = classification['documents'] / total
        data_pct = classification['data'] / total
        
        if code_pct > 0.6:
            return 'code'
        elif doc_pct > 0.6:
            return 'documentation'
        elif data_pct > 0.6:
            return 'data'
        else:
            return 'mixed'
    
    async def _ai_organize_content(
        self, 
        assets: List[Dict[str, Any]], 
        context: Dict[str, Any],
        goal_info: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Use AI to organize content structure"""
        try:
            # Prepare asset summary for AI
            asset_summary = []
            for i, asset in enumerate(assets[:20]):  # Limit to prevent token overflow
                asset_summary.append({
                    'index': i,
                    'type': asset.get('asset_type'),
                    'name': asset.get('asset_name'),
                    'description': asset.get('description', ''),
                    'size': asset.get('byte_size', 0),
                    'quality': asset.get('quality_score', 0)
                })
            
            prompt = f"""Analyze these assets and create an optimal organization structure for a professional deliverable.

Assets to organize:
{json.dumps(asset_summary, indent=2)}

Context:
- Domain: {context.get('domain', 'General')}
- Project: {context.get('project_name', 'Unknown')}
- Workspace: {context.get('workspace_name', 'Unknown')}

Goal alignment: {json.dumps(goal_info) if goal_info else 'No specific goal'}

Create a logical structure that:
1. Groups related assets together
2. Creates a clear narrative flow
3. Highlights most valuable/important assets
4. Suggests section titles and hierarchy
5. Identifies dependencies between assets

Return a JSON structure:
{{
    "title": "Deliverable title",
    "sections": [
        {{
            "section_title": "Section name",
            "description": "What this section contains",
            "asset_indices": [0, 2, 5],  // Indices of assets for this section
            "priority": "high|medium|low",
            "order": 1
        }}
    ],
    "executive_highlights": ["key point 1", "key point 2"],
    "recommended_flow": "Description of how to read/use this deliverable",
    "key_assets": [0, 1],  // Indices of most important assets
    "dependencies": {{"asset_index": [dependent_indices]}}
}}"""

            agent = {
                "name": "ContentOrganizerAgent",
                "model": "gpt-4o-mini",
                "instructions": "You are an expert at organizing technical content into professional deliverables."
            }
            
            response = await ai_provider_manager.call_ai(
                provider_type='openai_sdk',
                agent=agent,
                prompt=prompt,
                max_tokens=1500,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            if response and isinstance(response, dict):
                return response
            
            # Fallback structure
            return self._create_fallback_structure(assets)
            
        except Exception as e:
            logger.error(f"AI organization failed: {e}")
            return self._create_fallback_structure(assets)
    
    def _create_fallback_structure(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a simple fallback organization structure"""
        return {
            "title": "Project Deliverable",
            "sections": [
                {
                    "section_title": "All Assets",
                    "description": "Complete list of project assets",
                    "asset_indices": list(range(len(assets))),
                    "priority": "high",
                    "order": 1
                }
            ],
            "executive_highlights": ["Project assets compiled"],
            "recommended_flow": "Review assets in order",
            "key_assets": [0] if assets else [],
            "dependencies": {}
        }
    
    async def _aggregate_code_assets(
        self, 
        assets: List[Dict[str, Any]], 
        structure: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Aggregate code assets into technical documentation"""
        sections = []
        
        sections.append(f"# {structure.get('title', 'Code Deliverable')}")
        sections.append(f"\n{structure.get('recommended_flow', '')}\n")
        
        # Group code by language
        code_by_language = {}
        for asset in assets:
            if asset.get('asset_type') == 'code':
                lang = asset.get('language', 'unknown')
                if lang not in code_by_language:
                    code_by_language[lang] = []
                code_by_language[lang].append(asset)
        
        # Create sections by language
        for lang, code_assets in code_by_language.items():
            sections.append(f"\n## {lang.capitalize()} Code")
            
            for asset in code_assets:
                sections.append(f"\n### {asset.get('asset_name', 'Code Snippet')}")
                if asset.get('description'):
                    sections.append(f"*{asset['description']}*")
                sections.append(f"\n```{lang}")
                sections.append(asset.get('content', ''))
                sections.append("```\n")
        
        # Add non-code assets as appendix
        other_assets = [a for a in assets if a.get('asset_type') != 'code']
        if other_assets:
            sections.append("\n## Additional Resources")
            for asset in other_assets:
                sections.append(f"\n### {asset.get('asset_name', 'Resource')}")
                sections.append(asset.get('content', '')[:500] + "...")
        
        return "\n".join(sections)
    
    async def _aggregate_documentation_assets(
        self, 
        assets: List[Dict[str, Any]], 
        structure: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Aggregate documentation assets into comprehensive guide"""
        sections = []
        
        sections.append(f"# {structure.get('title', 'Documentation Deliverable')}")
        
        # Process structured sections
        for section in structure.get('sections', []):
            sections.append(f"\n## {section['section_title']}")
            if section.get('description'):
                sections.append(f"*{section['description']}*\n")
            
            # Add assets for this section
            for idx in section.get('asset_indices', []):
                if idx < len(assets):
                    asset = assets[idx]
                    if asset.get('asset_type') in ['documents', 'reference']:
                        sections.append(asset.get('content', ''))
                    else:
                        # Include non-doc assets as references
                        sections.append(f"\n**{asset.get('asset_name', 'Asset')}**")
                        sections.append(f"Type: {asset.get('asset_type', 'unknown')}")
                        if asset.get('content'):
                            sections.append("```")
                            sections.append(asset['content'][:300] + "...")
                            sections.append("```")
        
        return "\n".join(sections)
    
    async def _aggregate_data_assets(
        self, 
        assets: List[Dict[str, Any]], 
        structure: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Aggregate data assets into data report"""
        sections = []
        
        sections.append(f"# {structure.get('title', 'Data Analysis Deliverable')}")
        sections.append("\n## Data Summary")
        
        # Aggregate all data structures
        data_assets = [a for a in assets if a.get('asset_type') == 'data']
        
        for i, asset in enumerate(data_assets, 1):
            sections.append(f"\n### Dataset {i}: {asset.get('asset_name', 'Data')}")
            
            # Try to parse and summarize data
            try:
                if asset.get('format') == 'json':
                    data = json.loads(asset.get('content', '{}'))
                    sections.append(f"- Type: {type(data).__name__}")
                    if isinstance(data, dict):
                        sections.append(f"- Keys: {', '.join(list(data.keys())[:10])}")
                    elif isinstance(data, list):
                        sections.append(f"- Items: {len(data)}")
                sections.append("\n```json")
                sections.append(asset.get('content', ''))
                sections.append("```\n")
            except:
                sections.append("```")
                sections.append(asset.get('content', ''))
                sections.append("```\n")
        
        return "\n".join(sections)
    
    async def _aggregate_mixed_assets(
        self, 
        assets: List[Dict[str, Any]], 
        structure: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Aggregate mixed asset types into comprehensive deliverable"""
        sections = []
        
        sections.append(f"# {structure.get('title', 'Project Deliverable')}")
        
        # Executive highlights
        highlights = structure.get('executive_highlights', [])
        if highlights:
            sections.append("\n## Executive Summary")
            for highlight in highlights:
                sections.append(f"- {highlight}")
        
        # Process sections according to AI organization
        for section in sorted(structure.get('sections', []), key=lambda x: x.get('order', 999)):
            sections.append(f"\n## {section['section_title']}")
            
            if section.get('description'):
                sections.append(f"*{section['description']}*\n")
            
            # Add assets for this section
            for idx in section.get('asset_indices', []):
                if idx < len(assets):
                    asset = assets[idx]
                    sections.append(f"\n### {asset.get('asset_name', f'Asset {idx+1}')}")
                    
                    # Add asset based on type
                    asset_type = asset.get('asset_type', 'unknown')
                    if asset_type == 'code':
                        lang = asset.get('language', 'text')
                        sections.append(f"```{lang}")
                        sections.append(asset.get('content', ''))
                        sections.append("```")
                    elif asset_type == 'data':
                        sections.append("```json")
                        sections.append(asset.get('content', ''))
                        sections.append("```")
                    else:
                        sections.append(asset.get('content', ''))
                    
                    sections.append("")  # Empty line
        
        return "\n".join(sections)
    
    async def _generate_executive_summary(
        self,
        aggregated_content: str,
        assets: List[Dict[str, Any]],
        context: Dict[str, Any],
        goal_info: Optional[Dict[str, Any]]
    ) -> str:
        """Generate executive summary using AI"""
        try:
            prompt = f"""Create a concise executive summary for this deliverable.

Deliverable contains:
- {len(assets)} total assets
- Asset types: {', '.join(set(a.get('asset_type', 'unknown') for a in assets))}
- Context: {context.get('domain', 'General')} domain, {context.get('project_name', 'Unknown project')}

Goal alignment: {json.dumps(goal_info) if goal_info else 'General project deliverable'}

Content preview (first 1000 chars):
{aggregated_content[:1000]}...

Create a 3-5 sentence executive summary that:
1. Clearly states what this deliverable contains
2. Highlights the business value
3. Indicates who should use it and how
4. Mentions any key findings or outputs

Keep it professional and actionable."""

            agent = {
                "name": "ExecutiveSummaryAgent",
                "model": "gpt-4o-mini",
                "instructions": "You create concise, impactful executive summaries."
            }
            
            response = await ai_provider_manager.call_ai(
                provider_type='openai_sdk',
                agent=agent,
                prompt=prompt,
                max_tokens=300,
                temperature=0.3
            )
            
            if response and isinstance(response, dict):
                return response.get('content', '').strip()
            
            return f"This deliverable contains {len(assets)} assets aggregated from project execution."
            
        except Exception as e:
            logger.error(f"Executive summary generation failed: {e}")
            return f"This deliverable contains {len(assets)} assets from the {context.get('project_name', 'project')}."
    
    def _create_deliverable_structure(
        self,
        executive_summary: str,
        aggregated_content: str,
        assets: List[Dict[str, Any]],
        context: Dict[str, Any],
        strategy: str
    ) -> Dict[str, Any]:
        """Create final deliverable structure"""
        return {
            'title': f"{context.get('project_name', 'Project')} Deliverable",
            'type': f'{strategy}_deliverable',
            'executive_summary': executive_summary,
            'content': aggregated_content,
            'assets_included': len(assets),
            'aggregation_strategy': strategy,
            'status': 'completed',
            'created_at': datetime.now().isoformat()
        }
    
    def _calculate_deliverable_quality(
        self, 
        deliverable: Dict[str, Any],
        assets: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate quality metrics for deliverable"""
        # Asset quality average
        asset_quality = sum(a.get('quality_score', 0) for a in assets) / max(1, len(assets))
        
        # Content completeness (based on size and structure)
        content_size = len(deliverable.get('content', ''))
        completeness = min(1.0, content_size / 5000)  # Expect at least 5000 chars
        
        # Diversity score (different asset types)
        asset_types = set(a.get('asset_type') for a in assets)
        diversity = len(asset_types) / 5  # Max 5 types expected
        
        # Overall score
        overall = (asset_quality * 0.4 + completeness * 0.3 + diversity * 0.3)
        
        return {
            'overall_score': overall,
            'asset_quality': asset_quality,
            'completeness': completeness,
            'diversity': diversity,
            'asset_count': len(assets)
        }
    
    def _generate_metadata(
        self,
        assets: List[Dict[str, Any]],
        context: Dict[str, Any],
        strategy: str
    ) -> Dict[str, Any]:
        """Generate deliverable metadata"""
        return {
            'generation_timestamp': datetime.now().isoformat(),
            'aggregation_strategy': strategy,
            'source_context': context,
            'asset_summary': {
                'total': len(assets),
                'by_type': self._classify_assets(assets),
                'quality_range': {
                    'min': min((a.get('quality_score', 0) for a in assets), default=0),
                    'max': max((a.get('quality_score', 0) for a in assets), default=0),
                    'avg': sum(a.get('quality_score', 0) for a in assets) / max(1, len(assets))
                }
            }
        }
    
    def _create_empty_deliverable(self, reason: str) -> Dict[str, Any]:
        """Create empty deliverable structure"""
        return {
            'title': 'Empty Deliverable',
            'type': 'empty',
            'executive_summary': reason,
            'content': f"No content available: {reason}",
            'assets_included': 0,
            'status': 'empty',
            'quality_metrics': {
                'overall_score': 0,
                'asset_quality': 0,
                'completeness': 0,
                'diversity': 0
            }
        }
    
    def _create_error_deliverable(self, error: str, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create error deliverable with partial content"""
        return {
            'title': 'Error in Deliverable Generation',
            'type': 'error',
            'executive_summary': f"Deliverable generation encountered an error: {error}",
            'content': f"Error occurred during aggregation. {len(assets)} assets were provided but could not be processed.",
            'assets_included': len(assets),
            'status': 'error',
            'error': error,
            'quality_metrics': {
                'overall_score': 0,
                'asset_quality': 0,
                'completeness': 0,
                'diversity': 0
            }
        }


# Create singleton instance
intelligent_aggregator = IntelligentDeliverableAggregator()