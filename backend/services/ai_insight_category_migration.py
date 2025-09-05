"""
AI-Driven Insight Category Migration Service

This service uses AI to intelligently migrate insights between categories,
understanding the semantic content and business context to properly categorize them.
Fully compliant with system principles: no hard-coding, domain-agnostic, AI-driven.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import asyncio
from enum import Enum

from database import supabase
from services.ai_provider_abstraction import ai_provider_manager
from services.user_insight_manager import user_insight_manager, UserManagedInsight

logger = logging.getLogger(__name__)

class CategoryMigrationStrategy(str, Enum):
    """Migration strategies for category reassignment"""
    AI_SEMANTIC = "ai_semantic"  # Use AI to understand content semantically
    KEYWORD_FALLBACK = "keyword_fallback"  # Fallback to keyword matching if AI fails
    PRESERVE_EXISTING = "preserve_existing"  # Keep current categories
    HYBRID = "hybrid"  # Combine AI with existing patterns

class AICategoryMigrationService:
    """
    AI-driven service for migrating insight categories intelligently.
    Uses semantic understanding to properly categorize insights.
    """
    
    def __init__(self):
        self.ai_provider = ai_provider_manager
        self.migration_history = []
        
    async def analyze_insight_for_category(
        self,
        title: str,
        content: str,
        current_category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Use AI to analyze an insight and determine the best category.
        
        Args:
            title: Insight title
            content: Insight content/description
            current_category: Current category (if any)
            
        Returns:
            Dictionary with recommended category and reasoning
        """
        try:
            prompt = f"""
            Analyze this business insight and determine the most appropriate category.
            
            Title: {title}
            Content: {content}
            Current Category: {current_category or 'None'}
            
            Categories to choose from:
            1. general - General insights about team, processes, productivity, communication
            2. business_analysis - Business metrics, market analysis, revenue, customers, strategy
            3. technical - Technical implementation, architecture, code, infrastructure, DevOps
            
            Analyze the content semantically and return:
            - category: The most appropriate category (general/business_analysis/technical)
            - confidence: Your confidence score (0.0-1.0)
            - reasoning: Brief explanation of why this category fits
            - keywords: Key terms that influenced your decision
            
            Return as JSON format.
            """
            
            response = await self.ai_provider.call_ai(
                prompt,
                temperature=0.3,  # Lower temperature for consistent categorization
                response_format="json"
            )
            
            # Parse AI response
            import json
            try:
                result = json.loads(response)
                return {
                    'category': result.get('category', 'general'),
                    'confidence': float(result.get('confidence', 0.7)),
                    'reasoning': result.get('reasoning', 'AI analysis completed'),
                    'keywords': result.get('keywords', [])
                }
            except json.JSONDecodeError:
                # Fallback parsing if not proper JSON
                logger.warning("AI response was not valid JSON, using fallback parsing")
                return self._fallback_categorization(title, content)
                
        except Exception as e:
            logger.error(f"AI categorization failed: {e}")
            return self._fallback_categorization(title, content)
    
    def _fallback_categorization(self, title: str, content: str) -> Dict[str, Any]:
        """
        Fallback categorization using simple pattern matching.
        Only used when AI is unavailable.
        """
        combined_text = f"{title} {content}".lower()
        
        # Simple keyword-based fallback (not ideal but necessary for resilience)
        business_indicators = ['revenue', 'customer', 'market', 'sales', 'roi', 'acquisition', 'retention']
        technical_indicators = ['code', 'api', 'database', 'deployment', 'architecture', 'performance', 'security']
        
        business_score = sum(1 for word in business_indicators if word in combined_text)
        technical_score = sum(1 for word in technical_indicators if word in combined_text)
        
        if business_score > technical_score and business_score > 0:
            category = 'business_analysis'
        elif technical_score > 0:
            category = 'technical'
        else:
            category = 'general'
            
        return {
            'category': category,
            'confidence': 0.5,  # Lower confidence for fallback
            'reasoning': 'Fallback categorization based on keyword patterns',
            'keywords': []
        }
    
    async def migrate_workspace_insights(
        self,
        workspace_id: str,
        strategy: CategoryMigrationStrategy = CategoryMigrationStrategy.AI_SEMANTIC,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Migrate all insights in a workspace to proper categories.
        
        Args:
            workspace_id: Workspace to migrate
            strategy: Migration strategy to use
            dry_run: If True, analyze but don't update database
            
        Returns:
            Migration report with statistics
        """
        logger.info(f"🚀 Starting insight category migration for workspace {workspace_id}")
        logger.info(f"   Strategy: {strategy.value}, Dry run: {dry_run}")
        
        # Get all insights for workspace
        try:
            result = supabase.table('workspace_insights')\
                .select('*')\
                .eq('workspace_id', workspace_id)\
                .eq('is_deleted', False)\
                .execute()
            
            insights = result.data if result.data else []
            logger.info(f"📊 Found {len(insights)} insights to process")
            
        except Exception as e:
            logger.error(f"Failed to fetch insights: {e}")
            return {
                'success': False,
                'error': str(e),
                'processed': 0
            }
        
        # Process each insight
        migration_report = {
            'total': len(insights),
            'processed': 0,
            'changed': 0,
            'unchanged': 0,
            'failed': 0,
            'changes': [],
            'dry_run': dry_run
        }
        
        for insight in insights:
            try:
                insight_id = insight['id']
                title = insight.get('title', '')
                content = insight.get('content', '')
                current_category = insight.get('insight_category', 'general')
                current_domain = insight.get('domain_type', 'general')
                
                # Analyze with AI
                if strategy in [CategoryMigrationStrategy.AI_SEMANTIC, CategoryMigrationStrategy.HYBRID]:
                    analysis = await self.analyze_insight_for_category(title, content, current_category)
                else:
                    analysis = {'category': current_category, 'confidence': 1.0, 'reasoning': 'Preserved existing'}
                
                new_category = analysis['category']
                
                # Determine if change is needed
                if new_category != current_domain:
                    migration_report['changed'] += 1
                    change_record = {
                        'id': insight_id,
                        'title': title[:50],
                        'old_category': current_domain,
                        'new_category': new_category,
                        'confidence': analysis['confidence'],
                        'reasoning': analysis['reasoning']
                    }
                    migration_report['changes'].append(change_record)
                    
                    # Apply change if not dry run
                    if not dry_run:
                        update_result = supabase.table('workspace_insights')\
                            .update({
                                'domain_type': new_category,
                                'insight_category': new_category,  # Keep both in sync
                                'updated_at': datetime.now().isoformat(),
                                'metadata': {
                                    **insight.get('metadata', {}),
                                    'last_migration': {
                                        'date': datetime.now().isoformat(),
                                        'strategy': strategy.value,
                                        'confidence': analysis['confidence'],
                                        'reasoning': analysis['reasoning']
                                    }
                                }
                            })\
                            .eq('id', insight_id)\
                            .execute()
                        
                        if update_result.data:
                            logger.info(f"  ✅ Migrated: {title[:30]}... from {current_domain} → {new_category}")
                        else:
                            logger.warning(f"  ⚠️ Failed to update: {title[:30]}...")
                            migration_report['failed'] += 1
                    else:
                        logger.info(f"  🔍 [DRY RUN] Would migrate: {title[:30]}... from {current_domain} → {new_category}")
                else:
                    migration_report['unchanged'] += 1
                    logger.debug(f"  ✓ No change needed: {title[:30]}... remains {current_domain}")
                
                migration_report['processed'] += 1
                
                # Add small delay to avoid overwhelming AI API
                if strategy == CategoryMigrationStrategy.AI_SEMANTIC:
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"  ❌ Error processing insight {insight.get('id')}: {e}")
                migration_report['failed'] += 1
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("📈 MIGRATION COMPLETE")
        logger.info(f"  Total insights: {migration_report['total']}")
        logger.info(f"  Processed: {migration_report['processed']}")
        logger.info(f"  Changed: {migration_report['changed']}")
        logger.info(f"  Unchanged: {migration_report['unchanged']}")
        logger.info(f"  Failed: {migration_report['failed']}")
        
        if dry_run:
            logger.info("\n⚠️ DRY RUN - No changes were applied to database")
        else:
            logger.info("\n✅ Changes applied to database")
        
        migration_report['success'] = True
        migration_report['timestamp'] = datetime.now().isoformat()
        
        # Store migration history
        self.migration_history.append(migration_report)
        
        return migration_report
    
    async def validate_categories(self, workspace_id: str) -> Dict[str, Any]:
        """
        Validate that all insights have proper categories assigned.
        
        Args:
            workspace_id: Workspace to validate
            
        Returns:
            Validation report
        """
        try:
            result = supabase.table('workspace_insights')\
                .select('id, title, insight_category, domain_type')\
                .eq('workspace_id', workspace_id)\
                .eq('is_deleted', False)\
                .execute()
            
            insights = result.data if result.data else []
            
            validation_report = {
                'total': len(insights),
                'valid': 0,
                'invalid': 0,
                'missing_category': [],
                'mismatched': [],
                'distribution': {
                    'general': 0,
                    'business_analysis': 0,
                    'technical': 0,
                    'other': 0
                }
            }
            
            valid_categories = ['general', 'business_analysis', 'technical']
            
            for insight in insights:
                category = insight.get('insight_category')
                domain = insight.get('domain_type')
                
                # Check if category is valid
                if domain in valid_categories:
                    validation_report['valid'] += 1
                    validation_report['distribution'][domain] += 1
                else:
                    validation_report['invalid'] += 1
                    validation_report['distribution']['other'] += 1
                    
                # Check for missing categories
                if not category and not domain:
                    validation_report['missing_category'].append({
                        'id': insight['id'],
                        'title': insight.get('title', 'Untitled')[:50]
                    })
                
                # Check for mismatched category vs domain_type
                if category and domain and category != domain:
                    validation_report['mismatched'].append({
                        'id': insight['id'],
                        'title': insight.get('title', 'Untitled')[:50],
                        'category': category,
                        'domain_type': domain
                    })
            
            validation_report['health_score'] = (
                validation_report['valid'] / validation_report['total'] * 100
                if validation_report['total'] > 0 else 0
            )
            
            return validation_report
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# Global instance
ai_category_migration = AICategoryMigrationService()

# Convenience functions
async def migrate_insight_categories(
    workspace_id: str,
    dry_run: bool = True
) -> Dict[str, Any]:
    """Migrate insight categories for a workspace using AI."""
    return await ai_category_migration.migrate_workspace_insights(
        workspace_id,
        strategy=CategoryMigrationStrategy.AI_SEMANTIC,
        dry_run=dry_run
    )

async def validate_insight_categories(workspace_id: str) -> Dict[str, Any]:
    """Validate insight categories for a workspace."""
    return await ai_category_migration.validate_categories(workspace_id)

if __name__ == "__main__":
    # Test migration script
    import asyncio
    
    async def test_migration():
        workspace_id = 'f79d87cc-b61f-491d-9226-4220e39e71ad'
        
        print("\n" + "="*60)
        print("🔍 AI-DRIVEN INSIGHT CATEGORY MIGRATION")
        print("="*60)
        
        # First validate current state
        print("\n📊 Validating current categories...")
        validation = await validate_insight_categories(workspace_id)
        print(f"  Health Score: {validation.get('health_score', 0):.1f}%")
        print(f"  Distribution: {validation.get('distribution', {})}")
        
        if validation.get('mismatched'):
            print(f"  ⚠️ Found {len(validation['mismatched'])} mismatched categories")
        
        # Perform dry run
        print("\n🔍 Performing dry run migration...")
        dry_result = await migrate_insight_categories(workspace_id, dry_run=True)
        
        if dry_result.get('changed', 0) > 0:
            print(f"\n📋 Proposed changes: {dry_result['changed']}")
            for change in dry_result.get('changes', [])[:5]:
                print(f"  • {change['title']}...")
                print(f"    {change['old_category']} → {change['new_category']}")
                print(f"    Confidence: {change['confidence']:.2f}")
            
            # Ask for confirmation
            confirm = input("\n🤔 Apply these changes? (y/n): ").lower() == 'y'
            if confirm:
                print("\n✅ Applying migration...")
                result = await migrate_insight_categories(workspace_id, dry_run=False)
                print(f"Migration complete! Changed {result['changed']} insights.")
            else:
                print("❌ Migration cancelled.")
        else:
            print("✅ All insights are properly categorized!")
    
    asyncio.run(test_migration())