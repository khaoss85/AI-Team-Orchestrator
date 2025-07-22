#!/usr/bin/env python3
"""
🔧 AZIONE 3.2: Populate Quality Rules Database (Final Version)
Populates the database with quality rules using the correct database schema
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import List, Dict, Any
import sys
import os
import uuid

# Add backend to path
sys.path.append(os.path.dirname(__file__))

from database import supabase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class FinalQualityRulesPopulator:
    """Populates the database with quality rules using the correct database schema"""
    
    def __init__(self):
        self.quality_rules_definitions = {
            "code": [
                {
                    "rule_name": "Code Syntax Validation",
                    "rule_description": "Validates code syntax, proper indentation, and absence of syntax errors",
                    "ai_validation_prompt": "Check that this code has valid syntax, proper indentation, and no syntax errors. Return a score from 0-1 where 1 means perfect syntax.",
                    "validation_model": "gpt-4o-mini",
                    "validation_config": {"check_syntax": True, "check_indentation": True, "check_errors": True},
                    "threshold_score": 0.9,
                    "weight": 3,
                    "rule_order": 1,
                    "failure_action": "block",
                    "auto_learning_enabled": True,
                    "success_patterns": ["valid_syntax", "proper_indentation", "no_errors"],
                    "failure_lessons": ["syntax_errors", "indentation_issues", "compilation_errors"],
                    "language_agnostic": False,
                    "domain_agnostic": True
                },
                {
                    "rule_name": "Code Completeness Check",
                    "rule_description": "Ensures code is complete without placeholders or incomplete implementations",
                    "ai_validation_prompt": "Verify that this code is complete with no placeholders like 'TODO', '# placeholder', or incomplete functions. Check for proper imports and complete implementation.",
                    "validation_model": "gpt-4o-mini",
                    "validation_config": {"check_placeholders": True, "check_completeness": True, "check_imports": True},
                    "threshold_score": 0.8,
                    "weight": 2,
                    "rule_order": 2,
                    "failure_action": "warn",
                    "auto_learning_enabled": True,
                    "success_patterns": ["complete_implementation", "no_placeholders", "proper_imports"],
                    "failure_lessons": ["incomplete_code", "placeholder_content", "missing_imports"],
                    "language_agnostic": False,
                    "domain_agnostic": True
                },
                {
                    "rule_name": "Code Quality Standards",
                    "rule_description": "Evaluates code quality including readability, naming conventions, and best practices",
                    "ai_validation_prompt": "Evaluate the code quality including readability, proper variable naming, good structure, and adherence to best practices.",
                    "validation_model": "gpt-4o-mini",
                    "validation_config": {"check_readability": True, "check_naming": True, "check_structure": True},
                    "threshold_score": 0.7,
                    "weight": 1,
                    "rule_order": 3,
                    "failure_action": "warn",
                    "auto_learning_enabled": True,
                    "success_patterns": ["good_naming", "clear_structure", "readable_code"],
                    "failure_lessons": ["poor_naming", "unclear_structure", "unreadable_code"],
                    "language_agnostic": False,
                    "domain_agnostic": True
                }
            ],
            "json": [
                {
                    "rule_name": "JSON Syntax Validation",
                    "rule_description": "Validates JSON syntax and formatting",
                    "ai_validation_prompt": "Verify that this JSON is syntactically valid, properly formatted, and contains no syntax errors.",
                    "validation_model": "gpt-4o-mini",
                    "validation_config": {"check_syntax": True, "check_formatting": True},
                    "threshold_score": 0.95,
                    "weight": 3,
                    "rule_order": 1,
                    "failure_action": "block",
                    "auto_learning_enabled": True,
                    "success_patterns": ["valid_json", "proper_formatting"],
                    "failure_lessons": ["syntax_errors", "formatting_issues"],
                    "language_agnostic": True,
                    "domain_agnostic": True
                },
                {
                    "rule_name": "JSON Completeness Check",
                    "rule_description": "Ensures JSON contains required fields and proper data types",
                    "ai_validation_prompt": "Check that this JSON contains all required fields, proper data types, and no empty or null values where content is expected.",
                    "validation_model": "gpt-4o-mini",
                    "validation_config": {"check_required_fields": True, "check_data_types": True},
                    "threshold_score": 0.8,
                    "weight": 2,
                    "rule_order": 2,
                    "failure_action": "warn",
                    "auto_learning_enabled": True,
                    "success_patterns": ["complete_fields", "proper_types"],
                    "failure_lessons": ["missing_fields", "wrong_types", "empty_values"],
                    "language_agnostic": True,
                    "domain_agnostic": True
                }
            ],
            "configuration": [
                {
                    "rule_name": "Configuration Completeness",
                    "rule_description": "Ensures configuration files are complete and properly structured",
                    "ai_validation_prompt": "Verify that this configuration is complete with all necessary settings, default values, and proper structure.",
                    "validation_model": "gpt-4o-mini",
                    "validation_config": {"check_completeness": True, "check_structure": True},
                    "threshold_score": 0.85,
                    "weight": 2,
                    "rule_order": 1,
                    "failure_action": "warn",
                    "auto_learning_enabled": True,
                    "success_patterns": ["complete_settings", "proper_structure"],
                    "failure_lessons": ["missing_settings", "poor_structure"],
                    "language_agnostic": True,
                    "domain_agnostic": True
                },
                {
                    "rule_name": "Configuration Security",
                    "rule_description": "Checks for security issues in configuration files",
                    "ai_validation_prompt": "Check for security issues in configuration including hardcoded secrets, insecure defaults, and proper use of environment variables.",
                    "validation_model": "gpt-4o-mini",
                    "validation_config": {"check_secrets": True, "check_security": True},
                    "threshold_score": 0.9,
                    "weight": 3,
                    "rule_order": 2,
                    "failure_action": "block",
                    "auto_learning_enabled": True,
                    "success_patterns": ["no_hardcoded_secrets", "secure_defaults", "env_variables"],
                    "failure_lessons": ["hardcoded_secrets", "insecure_defaults", "missing_env_vars"],
                    "language_agnostic": True,
                    "domain_agnostic": True
                }
            ],
            "api_spec": [
                {
                    "rule_name": "API Documentation Quality",
                    "rule_description": "Evaluates API documentation completeness and quality",
                    "ai_validation_prompt": "Evaluate the API documentation quality including clear descriptions, examples, and error handling documentation.",
                    "validation_model": "gpt-4o-mini",
                    "validation_config": {"check_documentation": True, "check_examples": True},
                    "threshold_score": 0.8,
                    "weight": 2,
                    "rule_order": 1,
                    "failure_action": "warn",
                    "auto_learning_enabled": True,
                    "success_patterns": ["clear_documentation", "good_examples", "error_handling"],
                    "failure_lessons": ["poor_documentation", "missing_examples", "no_error_handling"],
                    "language_agnostic": True,
                    "domain_agnostic": False
                }
            ],
            "test_case": [
                {
                    "rule_name": "Test Coverage Quality",
                    "rule_description": "Evaluates test coverage and quality",
                    "ai_validation_prompt": "Evaluate the test coverage including comprehensive coverage, edge cases, and error scenarios.",
                    "validation_model": "gpt-4o-mini",
                    "validation_config": {"check_coverage": True, "check_edge_cases": True},
                    "threshold_score": 0.8,
                    "weight": 2,
                    "rule_order": 1,
                    "failure_action": "warn",
                    "auto_learning_enabled": True,
                    "success_patterns": ["comprehensive_coverage", "edge_cases", "error_scenarios"],
                    "failure_lessons": ["poor_coverage", "missing_edge_cases", "no_error_tests"],
                    "language_agnostic": False,
                    "domain_agnostic": True
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
    
    async def populate_quality_rules(self):
        """Populate the database with quality rules"""
        logger.info("🔧 Starting quality rules population with correct schema...")
        
        total_rules_created = 0
        total_rules_skipped = 0
        
        for asset_type, rules_data in self.quality_rules_definitions.items():
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
                    # Prepare rule data for insertion using correct schema
                    rule_dict = {
                        "id": str(uuid.uuid4()),
                        "asset_type": asset_type,
                        "rule_name": rule_data["rule_name"],
                        "rule_description": rule_data["rule_description"],
                        "ai_validation_prompt": rule_data["ai_validation_prompt"],
                        "validation_model": rule_data["validation_model"],
                        "validation_config": rule_data["validation_config"],
                        "threshold_score": rule_data["threshold_score"],
                        "weight": rule_data["weight"],
                        "is_active": True,
                        "rule_order": rule_data["rule_order"],
                        "failure_action": rule_data["failure_action"],
                        "auto_learning_enabled": rule_data["auto_learning_enabled"],
                        "success_patterns": rule_data["success_patterns"],
                        "failure_lessons": rule_data["failure_lessons"],
                        "language_agnostic": rule_data["language_agnostic"],
                        "domain_agnostic": rule_data["domain_agnostic"],
                        "created_at": datetime.now().isoformat()
                    }
                    
                    # Insert to database
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
            "asset_types_processed": len(self.quality_rules_definitions)
        }
    
    async def verify_quality_rules(self):
        """Verify that quality rules were created correctly"""
        logger.info("🔍 Verifying quality rules...")
        
        verification_results = {}
        
        for asset_type in self.quality_rules_definitions.keys():
            try:
                rules = await self.get_existing_rules(asset_type)
                verification_results[asset_type] = {
                    "count": len(rules),
                    "rules": [{"name": rule.get("rule_name", "unknown"), "threshold": rule.get("threshold_score", 0)} for rule in rules]
                }
                logger.info(f"✅ {asset_type}: {len(rules)} rules verified")
            except Exception as e:
                logger.error(f"❌ Failed to verify rules for {asset_type}: {e}")
                verification_results[asset_type] = {"error": str(e)}
        
        return verification_results

async def main():
    """Main function to populate quality rules"""
    logger.info("🚀 Starting Final Quality Rules Database Population")
    
    populator = FinalQualityRulesPopulator()
    
    try:
        # Populate quality rules
        results = await populator.populate_quality_rules()
        
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
        
        if results['total_created'] > 0:
            logger.info("✅ Quality rules population completed successfully!")
            logger.info("🎯 AZIONE 3.2 COMPLETED: Quality rules database populated instead of using fallbacks")
        else:
            logger.info("ℹ️ No new quality rules created (existing rules found)")
        
    except Exception as e:
        logger.error(f"❌ Quality rules population failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())