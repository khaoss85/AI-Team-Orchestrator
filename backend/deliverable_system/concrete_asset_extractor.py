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
            # FIXED: Ensure content is always a string
            if not isinstance(content, str):
                if isinstance(content, dict):
                    content = json.dumps(content, indent=2, default=str)
                elif isinstance(content, list):
                    if all(isinstance(item, str) for item in content):
                        content = '\n'.join(content)
                    else:
                        content = json.dumps(content, indent=2, default=str)
                else:
                    content = str(content)
            
            logger.info("🔍 Starting asset extraction from content")
            
            # Step 1: AI-powered content analysis
            ai_extracted = await self._ai_analyze_content(content, context)
            
            # Step 2: Pattern-based extraction
            pattern_extracted = await self._pattern_based_extraction(content)
            
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
            # Domain-agnostic AI analysis - removed hard-coded business bias
            domain_context = context.get('domain', 'unknown') if context else 'unknown'
            task_type = context.get('task_name', 'general') if context else 'general'
            
            prompt = f"""Analyze the following content and extract ALL concrete, usable assets without domain bias.

Content to analyze:
{content[:4000]}  # Limit for token management

Context: Task type: {task_type}, Domain: {domain_context}

Extract any concrete assets that could be valuable, including:
- Structured information (lists, tables, records)
- Contact or reference information  
- Process descriptions or workflows
- Data structures or specifications
- Documentation or guides
- Code snippets or technical content
- Any organized, actionable content

Evaluate each potential asset independently based on:
- Completeness and specificity
- Actionability and usefulness
- Organization and structure
- Domain relevance (if known)

For each asset found, provide:
- asset_type: Classify based on content structure (data|document|code|reference|process|list|other)
- asset_name: A descriptive name based on actual content
- content: The exact content (preserve all formatting)
- language: Programming language if applicable
- description: What this asset contains and its potential value
- value_score: 1-10 rating based on completeness and usefulness

Return as JSON object with "assets" array. Focus on CONCRETE, SPECIFIC content - avoid generic or placeholder material."""

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
            
            if response:
                # Handle both list and dict responses from AI
                if isinstance(response, list):
                    assets_data = response
                elif isinstance(response, dict):
                    assets_data = response.get('assets', [])
                else:
                    assets_data = []

                if isinstance(assets_data, list):
                    return [self._format_ai_asset(asset) for asset in assets_data]
            
            return []
            
        except Exception as e:
            logger.error(f"AI content analysis failed: {e}")
            return []
    
    async def _pattern_based_extraction(self, content: str) -> List[Dict[str, Any]]:
        """Extract assets using regex patterns"""
        assets = []
        
        try:
            # Extract code blocks
            for lang, pattern in self.extraction_patterns['code'].items():
                if lang == 'generic':
                    matches = re.findall(pattern, content, re.DOTALL | re.MULTILINE)
                    for match in matches:
                        language, code = match
                        # Ensure code is a string before strip
                        code_str = str(code) if not isinstance(code, str) else code
                        assets.append({
                            'asset_type': 'code',
                            'asset_name': f'{language}_snippet',
                            'content': code_str.strip(),
                            'language': language,
                            'extraction_method': 'pattern',
                            'confidence': 0.9
                        })
                else:
                    matches = re.findall(pattern, content, re.DOTALL)
                    for i, match in enumerate(matches):
                        # Ensure match is a string before strip
                        match_str = str(match) if not isinstance(match, str) else match
                        assets.append({
                            'asset_type': 'code',
                            'asset_name': f'{lang}_snippet_{i+1}',
                            'content': match_str.strip(),
                            'language': lang,
                            'extraction_method': 'pattern',
                            'confidence': 0.95
                        })
            
            # Extract JSON structures - ENHANCED
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
            
            # AI-driven structured content extraction - replaced hard-coded patterns
            await self._ai_extract_structured_content(content, assets)
            
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
            content = asset.get('content', '')
            # Convert to string if it's a dict or other non-string type - ROBUST VERSION
            try:
                if isinstance(content, dict):
                    import json
                    content_str = json.dumps(content, sort_keys=True, default=str)
                elif isinstance(content, list):
                    import json
                    content_str = json.dumps(content, sort_keys=True, default=str)
                else:
                    content_str = str(content)
                
                content_hash = hash(content_str)
                if content_hash not in seen_content:
                    seen_content.add(content_hash)
                    merged.append(asset)
            except Exception as e:
                logger.debug(f"Skipping unhashable asset content: {e}")
                # Still add the asset but with a random hash to avoid duplicates
                import time
                fallback_hash = hash(f"asset_{time.time()}_{len(merged)}")
                if fallback_hash not in seen_content:
                    seen_content.add(fallback_hash)
                    merged.append(asset)
        
        return merged
    
    async def _validate_and_enrich_assets(self, assets: List[Dict[str, Any]], original_content: str) -> List[Dict[str, Any]]:
        """Validate assets are real and enrich with metadata"""
        validated = []
        
        for asset in assets:
            # Skip if content is too short or looks like placeholder
            content = asset.get('content', '')
            # Convert to string if it's a dict or other non-string type for validation - ROBUST VERSION
            try:
                if isinstance(content, dict):
                    import json
                    content_str = json.dumps(content, sort_keys=True, default=str)
                elif isinstance(content, list):
                    import json
                    content_str = json.dumps(content, sort_keys=True, default=str)
                else:
                    content_str = str(content)
                
                if len(content_str) < 10 or await self._is_placeholder_content(content_str):
                    continue
                
                # Enrich asset metadata with safe hashing
                asset_hash = hash(content_str)
                asset['id'] = f"asset_{asset_hash}_{datetime.now().timestamp()}"
            except Exception as e:
                logger.debug(f"Error processing asset content for hashing: {e}")
                # Use timestamp as fallback ID
                asset['id'] = f"asset_fallback_{datetime.now().timestamp()}_{hash(str(asset))}"
                content_str = str(content) if content else "empty_content"
            asset['extracted_at'] = datetime.now().isoformat()
            asset['byte_size'] = len(content_str.encode('utf-8'))
            asset['line_count'] = content_str.count('\n') + 1
            
            # Calculate quality score (AI-driven)
            asset['quality_score'] = await self._calculate_asset_quality(asset)
            
            # Only include high-quality assets - FIXED: Lower threshold
            if asset['quality_score'] >= 0.5:  # Lowered from 0.6 to 0.5
                validated.append(asset)
                logger.debug(f"✅ Accepted asset '{asset.get('asset_name', 'unknown')}' with quality {asset['quality_score']:.2f}")
            else:
                logger.debug(f"❌ Rejected asset '{asset.get('asset_name', 'unknown')}' with quality {asset['quality_score']:.2f}")
        
        return validated
    
    async def _ai_extract_structured_content(self, content: str, assets: List[Dict[str, Any]]) -> None:
        """AI-driven extraction of structured content without hard-coded patterns"""
        try:
            # Use AI to identify and extract structured content
            extraction_prompt = f"""Analyze this content and identify any structured information that could be valuable business assets.

Content to analyze:
{content[:3000]}  # Limit for token management

Look for and extract:
- Contact information (names, emails, companies, roles)
- Lists or sequences (numbered or bulleted items)
- Structured data (tables, records, specifications)
- Business processes or workflows
- Any other organized information

For each structured element found, provide:
- element_type: The type of structured content
- element_name: A descriptive name
- content: The extracted content
- confidence: How confident you are this is valuable (0.0-1.0)

Only extract content that has clear business or informational value.

Respond with JSON:
{{
  "structured_elements": [
    {{
      "element_type": "contact_info|business_list|process|data_structure|other",
      "element_name": "descriptive name",
      "content": "extracted content",
      "confidence": 0.0-1.0,
      "business_value": "brief description of value"
    }}
  ]
}}"""

            agent = {
                "name": "StructuredContentExtractor",
                "model": "gpt-4o-mini",
                "instructions": "You are an expert at identifying structured business content. Focus on extracting valuable, organized information."
            }
            
            response = await ai_provider_manager.call_ai(
                provider_type='openai_sdk',
                agent=agent,
                prompt=extraction_prompt,
                max_tokens=1500,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            if response and isinstance(response, dict):
                response_content = response.get('content', response)
                if isinstance(response_content, str):
                    import json
                    extraction_result = json.loads(response_content)
                elif isinstance(response_content, dict):
                    extraction_result = response_content
                else:
                    return
                
                # Process extracted elements
                elements = extraction_result.get('structured_elements', [])
                for i, element in enumerate(elements):
                    if element.get('confidence', 0) >= 0.6:  # Only high-confidence extractions
                        assets.append({
                            'asset_type': 'structured_content',
                            'asset_name': element.get('element_name', f'structured_element_{i+1}'),
                            'content': element.get('content', ''),
                            'format': 'text',
                            'extraction_method': 'ai_structured',
                            'confidence': float(element.get('confidence', 0.8)),
                            'business_value': element.get('business_value', ''),
                            'detected_type': element.get('element_type', 'other')
                        })
                        
                logger.debug(f"AI extracted {len(elements)} structured elements from content")
                
        except Exception as e:
            logger.warning(f"AI structured content extraction failed: {e}")
            # Fallback to minimal pattern extraction if AI fails
            self._fallback_structured_extraction(content, assets)
    
    def _fallback_structured_extraction(self, content: str, assets: List[Dict[str, Any]]) -> None:
        """Minimal fallback extraction when AI fails - avoid hard-coded business rules"""
        try:
            # Only extract the most basic structured patterns
            import re
            
            # Generic list items (numbered or bulleted)
            list_pattern = r'^\s*(?:\d+[\.\)]\s*|[-•*]\s*)(.{20,}?)(?:\n|$)'
            matches = re.findall(list_pattern, content, re.MULTILINE)
            
            for i, match in enumerate(matches[:5]):  # Limit to avoid spam
                if len(match.strip()) > 20:
                    assets.append({
                        'asset_type': 'list_item',
                        'asset_name': f'list_item_{i+1}',
                        'content': match.strip(),
                        'format': 'text',
                        'extraction_method': 'fallback_pattern',
                        'confidence': 0.7
                    })
                    
        except Exception as e:
            logger.debug(f"Fallback structured extraction failed: {e}")

    def _format_ai_asset(self, raw_asset: Dict[str, Any]) -> Dict[str, Any]:
        """Format AI-extracted asset to standard structure with AI-driven type detection"""
        # AI already determined the asset type, so we trust its classification
        asset_type = raw_asset.get('asset_type', 'unknown')
        
        # Convert AI value_score (1-10) to confidence (0.0-1.0)
        value_score = raw_asset.get('value_score', 5)
        confidence = max(0.0, min(1.0, float(value_score) / 10.0))
        
        return {
            'asset_type': asset_type,
            'asset_name': raw_asset.get('asset_name', 'unnamed_asset'),
            'content': raw_asset.get('content', ''),
            'language': raw_asset.get('language'),
            'format': raw_asset.get('format', 'text'),
            'description': raw_asset.get('description', ''),
            'extraction_method': 'ai_analysis',
            'confidence': confidence,
            'ai_classification': True,  # Mark as AI-classified
            'ai_reasoning': raw_asset.get('description', '')  # Store AI's reasoning
        }
    
    async def _is_placeholder_content(self, content: str) -> bool:
        """AI-driven placeholder detection - no hard-coded lists"""
        try:
            # Use AI to detect placeholder/fake content
            placeholder_prompt = f"""Analyze this content and determine if it's placeholder, fake, or generic content.

Content to analyze:
{content[:500]}  # Limit for token management

Determine if this content is:
- Placeholder text (like "TODO", "TBD", "Lorem ipsum")
- Generic examples or templates without specific information
- Fake or dummy data
- Real, specific, actionable content

Respond with JSON:
{{
  "is_placeholder": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}}"""

            agent = {
                "name": "PlaceholderDetector",
                "model": "gpt-4o-mini",
                "instructions": "You are an expert at detecting placeholder, fake, or generic content vs real specific content."
            }
            
            response = await ai_provider_manager.call_ai(
                provider_type='openai_sdk',
                agent=agent,
                prompt=placeholder_prompt,
                max_tokens=150,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            if response and isinstance(response, dict):
                response_content = response.get('content', response)
                if isinstance(response_content, str):
                    import json
                    detection_result = json.loads(response_content)
                elif isinstance(response_content, dict):
                    detection_result = response_content
                else:
                    raise ValueError("Invalid AI response format")
                
                is_placeholder = detection_result.get('is_placeholder', False)
                confidence = detection_result.get('confidence', 0.8)
                
                # Only consider it placeholder if AI is confident
                return is_placeholder and confidence >= 0.7
                
        except Exception as e:
            logger.debug(f"AI placeholder detection failed, using fallback: {e}")
            
        # Simple fallback - check for very obvious placeholders only
        obvious_placeholders = ['lorem ipsum', 'todo', 'tbd', 'placeholder', 'xxx', 'example']
        content_lower = content.lower()
        return any(ph in content_lower for ph in obvious_placeholders)
    
    async def _calculate_asset_quality(self, asset: Dict[str, Any]) -> float:
        """AI-driven quality calculation - completely AI-powered without hard-coded rules"""
        try:
            # Use AI to evaluate asset quality based on content and context
            content = asset.get('content', '')
            if isinstance(content, dict):
                content_str = json.dumps(content, default=str)
            elif isinstance(content, list):
                content_str = json.dumps(content, default=str)
            else:
                content_str = str(content)
            
            # AI-driven quality assessment
            quality_prompt = f"""Analyze this asset and provide a quality score from 0.0 to 1.0.

Asset Type: {asset.get('asset_type', 'unknown')}
Asset Name: {asset.get('asset_name', 'unnamed')}
Content Size: {len(content_str)} characters
Extraction Method: {asset.get('extraction_method', 'unknown')}

Content:
{content_str[:2000]}  # Limit for token management

Evaluate quality based on:
1. Completeness and usefulness of content
2. Specificity vs generic/placeholder content
3. Business value and actionability
4. Structure and organization
5. Context appropriateness

Respond with JSON:
{{
  "quality_score": 0.0-1.0,
  "reasoning": "brief explanation of score",
  "completeness": 0.0-1.0,
  "business_value": 0.0-1.0,
  "specificity": 0.0-1.0
}}"""

            agent = {
                "name": "AssetQualityEvaluator",
                "model": "gpt-4o-mini",
                "instructions": "You are an expert at evaluating asset quality objectively. Focus on business value and concrete usability."
            }
            
            response = await ai_provider_manager.call_ai(
                provider_type='openai_sdk',
                agent=agent,
                prompt=quality_prompt,
                max_tokens=300,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            if response and isinstance(response, dict):
                response_content = response.get('content', response)
                if isinstance(response_content, str):
                    assessment = json.loads(response_content)
                elif isinstance(response_content, dict):
                    assessment = response_content
                else:
                    raise ValueError("Invalid AI response format")
                
                ai_score = float(assessment.get('quality_score', 0.8))
                logger.debug(f"AI quality score for {asset.get('asset_name', 'unknown')}: {ai_score:.2f} - {assessment.get('reasoning', 'No reasoning')}")
                return max(0.0, min(1.0, ai_score))
            
        except Exception as e:
            logger.warning(f"AI quality evaluation failed, using fallback: {e}")
            
        # Simple fallback for when AI fails - still avoid hard-coded business rules
        confidence = asset.get('confidence', 0.8)
        content_size = len(content_str) if 'content_str' in locals() else 0
        
        # Basic quality based on content presence and extraction confidence
        base_score = 0.6 + (confidence * 0.3)  # 0.6-0.9 range based on confidence
        
        # Size factor (logarithmic to avoid hard thresholds)
        if content_size > 0:
            size_factor = min(0.1, (content_size / 1000) * 0.1)  # Up to 0.1 bonus
            base_score += size_factor
            
        return max(0.0, min(1.0, base_score))
    
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
                    
                    # Convert result to string if it's a dict, list, or other object
                    task_result = task['result']
                    if isinstance(task_result, dict):
                        content_str = json.dumps(task_result, indent=2, default=str)
                    elif isinstance(task_result, list):
                        # Handle list results by joining or converting to JSON
                        if all(isinstance(item, str) for item in task_result):
                            content_str = '\n'.join(task_result)
                        else:
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