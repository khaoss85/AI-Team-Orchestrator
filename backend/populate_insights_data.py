#!/usr/bin/env python3
"""
Populate workspace with properly categorized insights for testing and demonstration.
This script creates a variety of insights across different categories to ensure
the Knowledge Management system displays correctly.
"""

import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
import random
from uuid import uuid4

from database import supabase
from models import InsightType
from services.user_insight_manager import user_insight_manager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample insights data with proper categorization
SAMPLE_INSIGHTS = [
    # General category insights
    {
        "title": "Team Communication Pattern Improvement",
        "content": "Weekly standup meetings have increased team synchronization by 40%. Team members report better understanding of project status and dependencies.",
        "category": "general",
        "domain_type": "general",
        "insight_type": InsightType.SUCCESS_PATTERN,
        "confidence_score": 0.85,
        "business_value_score": 0.75,
        "quantifiable_metrics": {
            "synchronization_increase": "40%",
            "meeting_effectiveness": "8/10"
        },
        "action_recommendations": [
            "Continue weekly standups",
            "Document key decisions from meetings",
            "Share meeting notes with absent team members"
        ]
    },
    {
        "title": "Documentation Best Practices",
        "content": "Teams that maintain up-to-date documentation reduce onboarding time by 60% and decrease support requests by 35%.",
        "category": "general",
        "domain_type": "general",
        "insight_type": InsightType.SUCCESS_PATTERN,
        "confidence_score": 0.90,
        "business_value_score": 0.85
    },
    {
        "title": "Remote Work Productivity Insights",
        "content": "Flexible working hours have led to a 25% increase in productivity metrics, with peak performance hours varying by team member.",
        "category": "general",
        "domain_type": "general",
        "insight_type": InsightType.DISCOVERY,
        "confidence_score": 0.75,
        "business_value_score": 0.70
    },
    {
        "title": "Project Risk Mitigation Strategy",
        "content": "Early identification of technical debt through code reviews has prevented 3 major production issues in the last quarter.",
        "category": "general",
        "domain_type": "general",
        "insight_type": InsightType.SUCCESS_PATTERN,
        "confidence_score": 0.88,
        "business_value_score": 0.92
    },
    {
        "title": "Knowledge Sharing Initiative Results",
        "content": "Monthly tech talks have increased cross-team collaboration by 45% and reduced duplicate work by 30%.",
        "category": "general",
        "domain_type": "general",
        "insight_type": InsightType.SUCCESS_PATTERN,
        "confidence_score": 0.82,
        "business_value_score": 0.78
    },
    
    # Business Analysis category insights
    {
        "title": "Customer Acquisition Cost Optimization",
        "content": "Digital marketing channels show 3x better ROI compared to traditional channels. Social media campaigns have the lowest CAC at $45 per customer.",
        "category": "business_analysis",
        "domain_type": "business_analysis",
        "insight_type": InsightType.OPTIMIZATION,
        "confidence_score": 0.92,
        "business_value_score": 0.95,
        "quantifiable_metrics": {
            "roi_improvement": "3x",
            "cac_social_media": "$45",
            "cac_traditional": "$135"
        }
    },
    {
        "title": "Market Expansion Opportunity Analysis",
        "content": "European market shows 150% growth potential based on current demand patterns. Early entry could capture 15% market share within 2 years.",
        "category": "business_analysis",
        "domain_type": "business_analysis",
        "insight_type": InsightType.DISCOVERY,
        "confidence_score": 0.78,
        "business_value_score": 0.88
    },
    {
        "title": "Revenue Stream Diversification Success",
        "content": "Subscription model introduction has created recurring revenue of $2M annually, improving cash flow predictability by 65%.",
        "category": "business_analysis",
        "domain_type": "business_analysis",
        "insight_type": InsightType.SUCCESS_PATTERN,
        "confidence_score": 0.95,
        "business_value_score": 0.98
    },
    {
        "title": "Customer Retention Analysis",
        "content": "Personalized onboarding programs increase customer lifetime value by 40%. Customers with dedicated success managers show 85% retention rate.",
        "category": "business_analysis",
        "domain_type": "business_analysis",
        "insight_type": InsightType.DISCOVERY,
        "confidence_score": 0.87,
        "business_value_score": 0.90
    },
    {
        "title": "Competitive Pricing Strategy Insights",
        "content": "Value-based pricing model outperforms cost-plus pricing by 28% in profit margins. Premium tier adoption increased by 15% after repositioning.",
        "category": "business_analysis",
        "domain_type": "business_analysis",
        "insight_type": InsightType.OPTIMIZATION,
        "confidence_score": 0.83,
        "business_value_score": 0.86
    },
    {
        "title": "Partnership Revenue Impact",
        "content": "Strategic partnerships contribute 35% of new customer acquisitions with 50% lower acquisition cost than direct sales.",
        "category": "business_analysis",
        "domain_type": "business_analysis",
        "insight_type": InsightType.SUCCESS_PATTERN,
        "confidence_score": 0.89,
        "business_value_score": 0.91
    },
    
    # Technical category insights
    {
        "title": "Microservices Architecture Benefits",
        "content": "Migration to microservices has reduced deployment time by 75% and improved system resilience with 99.9% uptime achieved.",
        "category": "technical",
        "domain_type": "technical",
        "insight_type": InsightType.SUCCESS_PATTERN,
        "confidence_score": 0.91,
        "business_value_score": 0.85,
        "quantifiable_metrics": {
            "deployment_time_reduction": "75%",
            "uptime": "99.9%",
            "rollback_time": "< 5 minutes"
        }
    },
    {
        "title": "Database Query Optimization Results",
        "content": "Index optimization and query refactoring reduced average response time from 2.3s to 0.4s, improving user experience significantly.",
        "category": "technical",
        "domain_type": "technical",
        "insight_type": InsightType.OPTIMIZATION,
        "confidence_score": 0.94,
        "business_value_score": 0.82
    },
    {
        "title": "CI/CD Pipeline Efficiency Gains",
        "content": "Automated testing in CI/CD pipeline catches 95% of bugs before production. Build time reduced from 45 minutes to 12 minutes.",
        "category": "technical",
        "domain_type": "technical",
        "insight_type": InsightType.SUCCESS_PATTERN,
        "confidence_score": 0.88,
        "business_value_score": 0.79
    },
    {
        "title": "API Rate Limiting Implementation",
        "content": "Rate limiting implementation prevented 12 potential DDoS attacks and reduced server costs by 30% through resource optimization.",
        "category": "technical",
        "domain_type": "technical",
        "insight_type": InsightType.SUCCESS_PATTERN,
        "confidence_score": 0.86,
        "business_value_score": 0.83
    },
    {
        "title": "Code Review Process Impact",
        "content": "Mandatory code reviews reduced production bugs by 60% and improved code quality metrics by 40%. Knowledge sharing increased across team.",
        "category": "technical",
        "domain_type": "technical",
        "insight_type": InsightType.SUCCESS_PATTERN,
        "confidence_score": 0.92,
        "business_value_score": 0.87
    },
    {
        "title": "Cloud Migration Cost Analysis",
        "content": "AWS migration reduced infrastructure costs by 45% while improving scalability. Auto-scaling handles 3x traffic spikes seamlessly.",
        "category": "technical",
        "domain_type": "technical",
        "insight_type": InsightType.OPTIMIZATION,
        "confidence_score": 0.90,
        "business_value_score": 0.93
    },
    {
        "title": "Security Audit Findings",
        "content": "Implementation of security best practices reduced vulnerability count by 80%. Zero critical vulnerabilities in last security audit.",
        "category": "technical",
        "domain_type": "technical",
        "insight_type": InsightType.SUCCESS_PATTERN,
        "confidence_score": 0.96,
        "business_value_score": 0.94
    },
    {
        "title": "Performance Monitoring Setup Benefits",
        "content": "Real-time monitoring alerts reduced mean time to resolution (MTTR) from 2 hours to 15 minutes for critical issues.",
        "category": "technical",
        "domain_type": "technical",
        "insight_type": InsightType.SUCCESS_PATTERN,
        "confidence_score": 0.85,
        "business_value_score": 0.88
    },
    {
        "title": "Test Coverage Improvement Impact",
        "content": "Increasing test coverage from 45% to 85% reduced regression bugs by 70% and improved release confidence significantly.",
        "category": "technical",
        "domain_type": "technical",
        "insight_type": InsightType.SUCCESS_PATTERN,
        "confidence_score": 0.89,
        "business_value_score": 0.81
    },
    {
        "title": "Container Orchestration Benefits",
        "content": "Kubernetes adoption improved resource utilization by 60% and reduced deployment failures by 90% through standardization.",
        "category": "technical",
        "domain_type": "technical",
        "insight_type": InsightType.OPTIMIZATION,
        "confidence_score": 0.87,
        "business_value_score": 0.84
    }
]

async def populate_insights(workspace_id: str, user_id: str = "system"):
    """Populate workspace with sample insights."""
    
    logger.info(f"🚀 Starting to populate insights for workspace {workspace_id}")
    
    # Clear existing insights for clean start (optional)
    clear_existing = input("Clear existing insights? (y/n): ").lower() == 'y'
    if clear_existing:
        try:
            # Soft delete existing insights
            result = supabase.table('workspace_insights')\
                .update({'is_deleted': True, 'deleted_at': datetime.now().isoformat()})\
                .eq('workspace_id', workspace_id)\
                .execute()
            logger.info(f"✅ Cleared {len(result.data) if result.data else 0} existing insights")
        except Exception as e:
            logger.warning(f"⚠️ Could not clear existing insights: {e}")
    
    created_count = 0
    failed_count = 0
    
    for idx, insight_data in enumerate(SAMPLE_INSIGHTS, 1):
        try:
            # Prepare insight for creation
            insight = {
                'workspace_id': workspace_id,
                'id': str(uuid4()),
                'title': insight_data['title'],
                'content': insight_data['content'],
                'insight_category': insight_data['category'],  # Use insight_category column
                'domain_type': insight_data['domain_type'],
                'insight_type': insight_data.get('insight_type', InsightType.DISCOVERY).value,
                'agent_role': 'system_curator',  # Required field
                'confidence_score': insight_data.get('confidence_score', 0.75),
                'business_value_score': insight_data.get('business_value_score', 0.70),
                'quantifiable_metrics': insight_data.get('quantifiable_metrics', {}),
                'metadata': {
                    'action_recommendations': insight_data.get('action_recommendations', []),
                    'tags': [],
                    'source': 'system_seed'
                },
                'relevance_tags': [],
                'created_by': user_id,
                'is_user_created': False,
                'is_user_modified': False,
                'is_deleted': False,
                'version_number': 1,
                'user_flags': {},
                'created_at': (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Insert into database
            result = supabase.table('workspace_insights').insert(insight).execute()
            
            if result.data:
                created_count += 1
                logger.info(f"  ✅ [{idx}/{len(SAMPLE_INSIGHTS)}] Created: {insight_data['title'][:50]}...")
            else:
                failed_count += 1
                logger.error(f"  ❌ [{idx}/{len(SAMPLE_INSIGHTS)}] Failed: {insight_data['title'][:50]}...")
                
        except Exception as e:
            failed_count += 1
            logger.error(f"  ❌ [{idx}/{len(SAMPLE_INSIGHTS)}] Error creating insight: {e}")
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info(f"📊 POPULATION COMPLETE")
    logger.info(f"  ✅ Successfully created: {created_count} insights")
    if failed_count > 0:
        logger.info(f"  ❌ Failed: {failed_count} insights")
    
    # Show distribution
    logger.info("\n📈 Category Distribution:")
    categories = {}
    for insight in SAMPLE_INSIGHTS[:created_count]:
        cat = insight['category']
        categories[cat] = categories.get(cat, 0) + 1
    
    for cat, count in sorted(categories.items()):
        logger.info(f"  • {cat}: {count} insights")
    
    logger.info("\n✨ Insights are now available in the Knowledge Base!")
    logger.info("   Navigate to the Knowledge Base chat and click 'Manage Insights' to view them.")
    
    return created_count

async def main():
    """Main execution function."""
    workspace_id = 'f79d87cc-b61f-491d-9226-4220e39e71ad'
    
    print("\n" + "="*60)
    print("🧠 AI TEAM ORCHESTRATOR - INSIGHTS DATA POPULATION")
    print("="*60)
    print(f"\nWorkspace ID: {workspace_id}")
    print(f"Total insights to create: {len(SAMPLE_INSIGHTS)}")
    print("\nThis will create properly categorized insights for:")
    print("  • General (5 insights)")
    print("  • Business Analysis (6 insights)")
    print("  • Technical (10 insights)")
    print("="*60 + "\n")
    
    proceed = input("Proceed with population? (y/n): ").lower() == 'y'
    if not proceed:
        print("❌ Population cancelled.")
        return
    
    created_count = await populate_insights(workspace_id)
    
    if created_count > 0:
        print("\n✅ Population successful! You can now:")
        print("1. Go to the Knowledge Base chat in the UI")
        print("2. Click 'Manage Insights' button")
        print("3. Browse insights by category (All, General, Business, Technical)")
        print("4. Test create, edit, delete, and bulk operations")

if __name__ == "__main__":
    asyncio.run(main())