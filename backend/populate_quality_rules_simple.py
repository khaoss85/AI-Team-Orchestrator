#!/usr/bin/env python3
"""
🔧 AZIONE 3.2: Populate Quality Rules Database (Simple Version)
Populates the database with basic quality rules using the existing schema
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import List, Dict, Any
import sys
import os
import uuid
from uuid import UUID

# Add backend to path
sys.path.append(os.path.dirname(__file__))

from database import supabase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class SimpleQualityRulesPopulator:
    """Populates the database with basic quality rules using existing schema"""
    
    def __init__(self):
        self.basic_quality_rules = {
            "code": [
                {
                    "rule_name": "Code Syntax Validation",
                    "asset_type": "code",
                    "ai_validation_prompt": "Check that this code has valid syntax, proper indentation, and no syntax errors. Return a score from 0-1 where 1 means perfect syntax.",
                    "threshold_score": 0.9,
                    "severity": "high",
                    "is_active": True
                },
                {
                    "rule_name": "Code Completeness Check",
                    "asset_type": "code",
                    "ai_validation_prompt": "Verify that this code is complete with no placeholders like 'TODO', '# placeholder', or incomplete functions. Check for proper imports and complete implementation.",
                    "threshold_score": 0.8,
                    "severity": "high",
                    "is_active": True
                },
                {
                    "rule_name": "Code Quality Standards",
                    "asset_type": "code",
                    "ai_validation_prompt": "Evaluate the code quality including readability, proper variable naming, good structure, and adherence to best practices.",
                    "threshold_score": 0.7,
                    "severity": "medium",
                    "is_active": True
                }
            ],
            "json": [
                {
                    "rule_name": "JSON Syntax Validation",
                    "asset_type": "json",
                    "ai_validation_prompt": "Verify that this JSON is syntactically valid, properly formatted, and contains no syntax errors.",
                    "threshold_score": 0.95,
                    "severity": "high",
                    "is_active": True
                },
                {
                    "rule_name": "JSON Completeness Check",
                    "asset_type": "json",
                    "ai_validation_prompt": "Check that this JSON contains all required fields, proper data types, and no empty or null values where content is expected.",
                    "threshold_score": 0.8,
                    "severity": "medium",
                    "is_active": True
                }
            ],
            "configuration": [
                {
                    "rule_name": "Configuration Completeness",
                    "asset_type": "configuration",
                    "ai_validation_prompt": "Verify that this configuration is complete with all necessary settings, default values, and proper structure.",
                    "threshold_score": 0.85,
                    "severity": "high",
                    "is_active": True
                },
                {
                    "rule_name": "Configuration Security",
                    "asset_type": "configuration",
                    "ai_validation_prompt": "Check for security issues in configuration including hardcoded secrets, insecure defaults, and proper use of environment variables.",
                    "threshold_score": 0.9,
                    "severity": "high",
                    "is_active": True
                }
            ],
            "api_spec": [
                {
                    "rule_name": "API Documentation Quality",
                    "asset_type": "api_spec",
                    "ai_validation_prompt": "Evaluate the API documentation quality including clear descriptions, examples, and error handling documentation.",
                    "threshold_score": 0.8,
                    "severity": "medium",
                    "is_active": True
                }
            ],
            "test_case": [
                {
                    "rule_name": "Test Coverage Quality",
                    "asset_type": "test_case",
                    "ai_validation_prompt": "Evaluate the test coverage including comprehensive coverage, edge cases, and error scenarios.",
                    "threshold_score": 0.8,
                    "severity": "high",
                    "is_active": True
                }
            ]
        }
    
    async def get_existing_rules(self, asset_type: str) -> List[Dict[str, Any]]:
        """Get existing quality rules for an asset type"""
        try:
            result = supabase.table("quality_rules").select("*").eq("asset_type", asset_type).execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error getting existing rules for {asset_type}: {e}")
            return []
    
    async def populate_basic_quality_rules(self):
        """Populate the database with basic quality rules"""
        logger.info("🔧 Starting basic quality rules population...")
        
        total_rules_created = 0
        total_rules_skipped = 0
        
        for asset_type, rules_data in self.basic_quality_rules.items():
            logger.info(f"📋 Processing {len(rules_data)} quality rules for asset type: {asset_type}")
            
            # Check if rules already exist for this asset type
            existing_rules = await self.get_existing_rules(asset_type)
            if existing_rules:
                logger.info(f"⚠️ {len(existing_rules)} quality rules already exist for {asset_type}, skipping...")
                total_rules_skipped += len(existing_rules)
                continue
            
            # Create rules for this asset type
            created_count = 0
            for rule_data in rules_data:
                try:
                    # Prepare rule data for insertion
                    rule_dict = rule_data.copy()
                    rule_dict['id'] = str(uuid.uuid4())
                    rule_dict['created_at'] = datetime.now().isoformat()
                    rule_dict['updated_at'] = datetime.now().isoformat()
                    
                    # Insert directly to database
                    result = supabase.table("quality_rules").insert(rule_dict).execute()
                    
                    if not result.data:
                        raise Exception("Insert failed - no data returned")
                    
                    created_count += 1
                    logger.info(f"✅ Created quality rule: {rule_data['rule_name']}")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to create quality rule '{rule_data['rule_name']}': {e}")
                    continue
            
            total_rules_created += created_count
            logger.info(f"✅ Created {created_count} quality rules for {asset_type}")
        
        logger.info(f"🎯 Quality rules population completed!")
        logger.info(f"   - Total rules created: {total_rules_created}")
        logger.info(f"   - Total rules skipped: {total_rules_skipped}")
        
        return {
            "total_created": total_rules_created,
            "total_skipped": total_rules_skipped,
            "asset_types_processed": len(self.basic_quality_rules)
        }
    
    async def verify_quality_rules(self):
        """Verify that quality rules were created correctly"""
        logger.info("🔍 Verifying quality rules...")
        
        verification_results = {}
        
        for asset_type in self.basic_quality_rules.keys():
            try:
                rules = await self.get_existing_rules(asset_type)
                verification_results[asset_type] = {
                    "count": len(rules),
                    "rules": [{"name": rule.get("rule_name", "unknown"), "severity": rule.get("severity", "unknown")} for rule in rules]
                }
                logger.info(f"✅ {asset_type}: {len(rules)} rules verified")
            except Exception as e:
                logger.error(f"❌ Failed to verify rules for {asset_type}: {e}")
                verification_results[asset_type] = {"error": str(e)}
        
        return verification_results

async def main():
    """Main function to populate quality rules"""
    logger.info("🚀 Starting Simple Quality Rules Database Population")
    
    populator = SimpleQualityRulesPopulator()
    
    try:
        # Populate quality rules
        results = await populator.populate_basic_quality_rules()
        
        # Verify the results
        verification = await populator.verify_quality_rules()
        
        logger.info("📊 Final Summary:")
        logger.info(f"   - Asset types processed: {results['asset_types_processed']}")
        logger.info(f"   - Total rules created: {results['total_created']}")
        logger.info(f"   - Total rules skipped: {results['total_skipped']}")
        
        logger.info("🔍 Verification Results:")
        for asset_type, verify_data in verification.items():
            if "error" in verify_data:
                logger.error(f"   - {asset_type}: ERROR - {verify_data['error']}")
            else:
                logger.info(f"   - {asset_type}: {verify_data['count']} rules verified")
        
        logger.info("✅ Quality rules population completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Quality rules population failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())