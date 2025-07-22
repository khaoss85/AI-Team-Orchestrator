"""
Concrete Asset Extractor - AI-Powered Real Asset Extraction
Extracts concrete assets (code, JSON, documents) from task outputs
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import asyncio

from services.ai_provider_abstraction import ai_provider_manager

logger = logging.getLogger(__name__)

class ConcreteAssetExtractor:
    """
    Extracts real, concrete assets from task execution outputs.
    Implements Pillar 12: Concrete Deliverables (no fake content)
    """
    
    def __init__(self):
        self.extraction_patterns = {
            'code': {
                'python': r'```python\n(.*?)```',
                'javascript': r'```javascript\n(.*?)```',
                'typescript': r'```typescript\n(.*?)```',
                'json': r'```json\n(.*?)```',
                'yaml': r'```yaml\n(.*?)```',
                'sql': r'```sql\n(.*?)```',
                'generic': r'```(\w+)\n(.*?)```'
            },
            'structured_data': {
                'json_inline': r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',
                'array': r'\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]',
            },
            'documents': {
                'markdown_section': r'^#{1,6}\s+(.+)$',
                'bullet_list': r'^\s*[-*+]\s+(.+)$',
                'numbered_list': r'^\s*\d+\.\s+(.+)$',
                'table': r'\|[^\n]+\|(?:\n\|[-:]+\|)?(?:\n\|[^\n]+\|)*'
            },
            'references': {
                'url': r'https?://[^\s<>"{}|\\^`\[\]]+',
                'file_path': r'(?:/[\w.-]+)+(?:\.\w+)?',
                'email': r'[\w._%+-]+@[\w.-]+\.[A-Z|a-z]{2,}'
            }
        }
    
    async def extract_assets(self, content: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Extract concrete assets from task output content using AI and pattern matching.
        
        Args:
            content: Raw output from task execution
            context: Optional context about the task/domain
            
        Returns:
            List of extracted assets with metadata
        """
        try:
            logger.info("🔍 Starting asset extraction from content")
            
            # Step 1: AI-powered content analysis
            ai_extracted = await self._ai_analyze_content(content, context)
            
            # Step 2: Pattern-based extraction
            pattern_extracted = self._pattern_based_extraction(content)
            
            # Step 3: Merge and deduplicate
            all_assets = self._merge_assets(ai_extracted, pattern_extracted)
            
            # Step 4: Validate and enrich assets
            validated_assets = await self._validate_and_enrich_assets(all_assets, content)
            
            logger.info(f"✅ Extracted {len(validated_assets)} concrete assets")
            return validated_assets
            
        except Exception as e:
            logger.error(f"Asset extraction failed: {e}")
            return []
    
    async def _ai_analyze_content(self, content: str, context: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Use AI to intelligently identify and extract assets from content"""
        try:
            prompt = f"""Analyze the following content and extract ALL concrete assets (code, data structures, documents, etc.).

Content to analyze:
{content[:4000]}  # Limit for token management

Context: {json.dumps(context) if context else 'General task output'}

Identify and extract:
1. Code snippets (any language)
2. JSON/YAML data structures
3. SQL queries
4. Configuration files
5. Documentation sections
6. API endpoints or specifications
7. File paths or references
8. Any other concrete deliverable assets

For each asset found, provide:
- asset_type: The type of asset (code, data, document, etc.)
- asset_name: A descriptive name
- content: The exact content (preserve formatting)
- language: Programming language if applicable
- description: What this asset does/represents
- value_score: 1-10 rating of how valuable/complete this asset is

Return as JSON array of assets. Focus on REAL, CONCRETE content only - no placeholders or examples."""

            agent = {
                "name": "AssetExtractorAgent",
                "model": "gpt-4o-mini",
                "instructions": "You are an expert at identifying and extracting valuable assets from text. Focus on concrete, usable content."
            }
            
            response = await ai_provider_manager.call_ai(
                provider_type='openai_sdk',
                agent=agent,
                prompt=prompt,
                max_tokens=2000,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            if response and isinstance(response, dict):
                assets_data = response.get('assets', [])
                if isinstance(assets_data, list):
                    return [self._format_ai_asset(asset) for asset in assets_data]
            
            return []
            
        except Exception as e:
            logger.error(f"AI content analysis failed: {e}")
            return []
    
    def _pattern_based_extraction(self, content: str) -> List[Dict[str, Any]]:
        """Extract assets using regex patterns"""
        assets = []
        
        try:
            # Extract code blocks
            for lang, pattern in self.extraction_patterns['code'].items():
                if lang == 'generic':
                    matches = re.findall(pattern, content, re.DOTALL | re.MULTILINE)
                    for match in matches:
                        language, code = match
                        assets.append({
                            'asset_type': 'code',
                            'asset_name': f'{language}_snippet',
                            'content': code.strip(),
                            'language': language,
                            'extraction_method': 'pattern',
                            'confidence': 0.9
                        })
                else:
                    matches = re.findall(pattern, content, re.DOTALL)
                    for i, match in enumerate(matches):
                        assets.append({
                            'asset_type': 'code',
                            'asset_name': f'{lang}_snippet_{i+1}',
                            'content': match.strip(),
                            'language': lang,
                            'extraction_method': 'pattern',
                            'confidence': 0.95
                        })
            
            # Extract JSON structures
            json_pattern = self.extraction_patterns['structured_data']['json_inline']
            potential_jsons = re.findall(json_pattern, content)
            for i, json_str in enumerate(potential_jsons):
                try:
                    # Validate it's actual JSON
                    parsed = json.loads(json_str)
                    assets.append({
                        'asset_type': 'data',
                        'asset_name': f'json_data_{i+1}',
                        'content': json.dumps(parsed, indent=2),
                        'format': 'json',
                        'extraction_method': 'pattern',
                        'confidence': 0.9
                    })
                except:
                    pass  # Not valid JSON
            
            # Extract URLs
            urls = re.findall(self.extraction_patterns['references']['url'], content)
            for url in urls:
                assets.append({
                    'asset_type': 'reference',
                    'asset_name': 'url_reference',
                    'content': url,
                    'format': 'url',
                    'extraction_method': 'pattern',
                    'confidence': 0.8
                })
            
            return assets
            
        except Exception as e:
            logger.error(f"Pattern extraction failed: {e}")
            return []
    
    def _merge_assets(self, ai_assets: List[Dict[str, Any]], pattern_assets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge AI and pattern-extracted assets, removing duplicates"""
        merged = []
        seen_content = set()
        
        # Prioritize AI-extracted assets (usually more context)
        for asset in ai_assets + pattern_assets:
            content_hash = hash(asset.get('content', ''))
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                merged.append(asset)
        
        return merged
    
    async def _validate_and_enrich_assets(self, assets: List[Dict[str, Any]], original_content: str) -> List[Dict[str, Any]]:
        """Validate assets are real and enrich with metadata"""
        validated = []
        
        for asset in assets:
            # Skip if content is too short or looks like placeholder
            content = asset.get('content', '')
            if len(content) < 10 or self._is_placeholder_content(content):
                continue
            
            # Enrich asset metadata
            asset['id'] = f"asset_{hash(content)}_{datetime.now().timestamp()}"
            asset['extracted_at'] = datetime.now().isoformat()
            asset['byte_size'] = len(content.encode('utf-8'))
            asset['line_count'] = content.count('\n') + 1
            
            # Calculate quality score
            asset['quality_score'] = self._calculate_asset_quality(asset)
            
            # Only include high-quality assets
            if asset['quality_score'] >= 0.6:
                validated.append(asset)
        
        return validated
    
    def _format_ai_asset(self, raw_asset: Dict[str, Any]) -> Dict[str, Any]:
        """Format AI-extracted asset to standard structure"""
        return {
            'asset_type': raw_asset.get('asset_type', 'unknown'),
            'asset_name': raw_asset.get('asset_name', 'unnamed_asset'),
            'content': raw_asset.get('content', ''),
            'language': raw_asset.get('language'),
            'format': raw_asset.get('format'),
            'description': raw_asset.get('description'),
            'extraction_method': 'ai',
            'confidence': raw_asset.get('value_score', 5) / 10.0
        }
    
    def _is_placeholder_content(self, content: str) -> bool:
        """Check if content is placeholder/fake"""
        placeholders = [
            'todo', 'tbd', 'placeholder', 'example', 'sample',
            'lorem ipsum', 'test data', 'dummy', 'fake',
            'your_', 'my_', '<insert', '[insert', 'xxx'
        ]
        
        content_lower = content.lower()
        return any(ph in content_lower for ph in placeholders)
    
    def _calculate_asset_quality(self, asset: Dict[str, Any]) -> float:
        """Calculate quality score for an asset"""
        score = 0.5  # Base score
        
        # Size bonus
        content_size = asset.get('byte_size', 0)
        if content_size > 100:
            score += 0.1
        if content_size > 500:
            score += 0.1
        
        # Type bonus
        if asset.get('asset_type') == 'code':
            score += 0.15
        elif asset.get('asset_type') == 'data':
            score += 0.1
        
        # Extraction confidence
        confidence = asset.get('confidence', 0.5)
        score = score * confidence
        
        # Cap at 1.0
        return min(1.0, score)
    
    async def extract_assets_from_task_batch(self, tasks: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Extract assets from multiple tasks in parallel"""
        try:
            logger.info(f"🔄 Extracting assets from {len(tasks)} tasks in batch")
            
            # Prepare extraction tasks
            extraction_tasks = []
            for task in tasks:
                if task.get('status') == 'completed' and task.get('result'):
                    context = {
                        'task_name': task.get('name'),
                        'task_type': task.get('type'),
                        'workspace_id': task.get('workspace_id')
                    }
                    
                    # Convert result to string if it's a dict or other object
                    task_result = task['result']
                    if isinstance(task_result, dict):
                        content_str = json.dumps(task_result, indent=2, default=str)
                    elif isinstance(task_result, str):
                        content_str = task_result
                    else:
                        content_str = str(task_result)
                    
                    extraction_tasks.append(
                        self.extract_assets(content_str, context)
                    )
            
            # Execute in parallel
            if extraction_tasks:
                results = await asyncio.gather(*extraction_tasks, return_exceptions=True)
                
                # Map results back to task IDs
                task_assets = {}
                for i, (task, result) in enumerate(zip(tasks, results)):
                    if isinstance(result, Exception):
                        logger.error(f"Asset extraction failed for task {task.get('id')}: {result}")
                        task_assets[task['id']] = []
                    else:
                        task_assets[task['id']] = result
                
                total_assets = sum(len(assets) for assets in task_assets.values())
                logger.info(f"✅ Extracted {total_assets} total assets from batch")
                return task_assets
            
            return {}
            
        except Exception as e:
            logger.error(f"Batch asset extraction failed: {e}")
            return {}


# Create singleton instance
concrete_asset_extractor = ConcreteAssetExtractor()