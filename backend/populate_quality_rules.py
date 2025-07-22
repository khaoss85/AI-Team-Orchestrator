#!/usr/bin/env python3
"""
🔧 AZIONE 3.2: Populate Quality Rules Database
Populates the database with comprehensive quality rules for different asset types
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

from database import create_quality_rule, get_quality_rules
from models import QualityRule

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class QualityRulesPopulator:
    """Populates the database with comprehensive quality rules"""
    
    def __init__(self):
        self.quality_rules_definitions = {
            "code": [
                {
                    "rule_name": "Code Syntax Validation",
                    "rule_type": "syntax_check",
                    "validation_logic": {
                        "check_type": "syntax",
                        "requirements": ["valid_syntax", "no_syntax_errors", "proper_indentation"]
                    },
                    "ai_validation_prompt": "Check that this code has valid syntax, proper indentation, and no syntax errors. Return a score from 0-1 where 1 means perfect syntax.",
                    "threshold_score": 0.9,
                    "severity": "high",
                    "rule_order": 1
                },
                {
                    "rule_name": "Code Completeness Check",
                    "rule_type": "completeness",
                    "validation_logic": {
                        "check_type": "completeness",
                        "requirements": ["no_placeholders", "complete_functions", "proper_imports"]
                    },
                    "ai_validation_prompt": "Verify that this code is complete with no placeholders like 'TODO', '# placeholder', or incomplete functions. Check for proper imports and complete implementation.",
                    "threshold_score": 0.8,
                    "severity": "high",
                    "rule_order": 2
                },
                {
                    "rule_name": "Code Quality Standards",
                    "rule_type": "quality_standards",
                    "validation_logic": {
                        "check_type": "quality",
                        "requirements": ["readable_code", "proper_naming", "good_structure"]
                    },
                    "ai_validation_prompt": "Evaluate the code quality including readability, proper variable naming, good structure, and adherence to best practices.",
                    "threshold_score": 0.7,
                    "severity": "medium",
                    "rule_order": 3
                },
                {
                    "rule_name": "Security Best Practices",
                    "rule_type": "security",
                    "validation_logic": {
                        "check_type": "security",
                        "requirements": ["no_hardcoded_secrets", "input_validation", "safe_practices"]
                    },
                    "ai_validation_prompt": "Check for security issues like hardcoded secrets, lack of input validation, or unsafe practices. Rate security compliance.",
                    "threshold_score": 0.8,
                    "severity": "high",
                    "rule_order": 4
                }
            ],
            "document": [
                {
                    "rule_name": "Document Completeness",
                    "rule_type": "completeness",
                    "validation_logic": {
                        "check_type": "completeness",
                        "requirements": ["complete_content", "no_placeholders", "proper_structure"]
                    },
                    "ai_validation_prompt": "Verify that this document is complete with no placeholders, has proper structure, and contains meaningful content.",
                    "threshold_score": 0.8,
                    "severity": "high",
                    "rule_order": 1
                },
                {
                    "rule_name": "Document Clarity",
                    "rule_type": "clarity",
                    "validation_logic": {
                        "check_type": "clarity",
                        "requirements": ["clear_language", "logical_flow", "proper_formatting"]
                    },
                    "ai_validation_prompt": "Evaluate the document for clarity, logical flow, proper formatting, and ease of understanding.",
                    "threshold_score": 0.7,
                    "severity": "medium",
                    "rule_order": 2
                },
                {
                    "rule_name": "Document Accuracy",
                    "rule_type": "accuracy",
                    "validation_logic": {
                        "check_type": "accuracy",
                        "requirements": ["factual_content", "consistent_information", "up_to_date"]
                    },
                    "ai_validation_prompt": "Check for factual accuracy, consistent information, and whether the content appears to be up-to-date and relevant.",
                    "threshold_score": 0.8,
                    "severity": "high",
                    "rule_order": 3
                }
            ],
            "json": [
                {
                    "rule_name": "JSON Syntax Validation",
                    "rule_type": "syntax_check",
                    "validation_logic": {
                        "check_type": "syntax",
                        "requirements": ["valid_json", "proper_formatting", "no_syntax_errors"]
                    },
                    "ai_validation_prompt": "Verify that this JSON is syntactically valid, properly formatted, and contains no syntax errors.",
                    "threshold_score": 0.95,
                    "severity": "high",
                    "rule_order": 1
                },
                {
                    "rule_name": "JSON Schema Completeness",
                    "rule_type": "completeness",
                    "validation_logic": {
                        "check_type": "completeness",
                        "requirements": ["required_fields", "proper_types", "no_empty_values"]
                    },
                    "ai_validation_prompt": "Check that this JSON contains all required fields, proper data types, and no empty or null values where content is expected.",
                    "threshold_score": 0.8,
                    "severity": "medium",
                    "rule_order": 2
                },
                {
                    "rule_name": "JSON Data Quality",
                    "rule_type": "data_quality",
                    "validation_logic": {
                        "check_type": "data_quality",
                        "requirements": ["meaningful_data", "consistent_format", "proper_structure"]
                    },
                    "ai_validation_prompt": "Evaluate the quality of data in this JSON including meaningfulness, consistency, and proper structure.",
                    "threshold_score": 0.7,
                    "severity": "medium",
                    "rule_order": 3
                }
            ],
            "api_spec": [
                {
                    "rule_name": "API Specification Completeness",
                    "rule_type": "completeness",
                    "validation_logic": {
                        "check_type": "completeness",
                        "requirements": ["endpoints_defined", "parameters_documented", "responses_specified"]
                    },
                    "ai_validation_prompt": "Verify that this API specification is complete with all endpoints, parameters, and responses properly documented.",
                    "threshold_score": 0.85,
                    "severity": "high",
                    "rule_order": 1
                },
                {
                    "rule_name": "API Documentation Quality",
                    "rule_type": "documentation",
                    "validation_logic": {
                        "check_type": "documentation",
                        "requirements": ["clear_descriptions", "examples_provided", "error_handling"]
                    },
                    "ai_validation_prompt": "Evaluate the API documentation quality including clear descriptions, examples, and error handling documentation.",
                    "threshold_score": 0.8,
                    "severity": "medium",
                    "rule_order": 2
                },
                {
                    "rule_name": "API Security Considerations",
                    "rule_type": "security",
                    "validation_logic": {
                        "check_type": "security",
                        "requirements": ["authentication_defined", "authorization_specified", "security_headers"]
                    },
                    "ai_validation_prompt": "Check that the API specification includes proper authentication, authorization, and security considerations.",
                    "threshold_score": 0.8,
                    "severity": "high",
                    "rule_order": 3
                }
            ],
            "database_schema": [
                {
                    "rule_name": "Schema Completeness",
                    "rule_type": "completeness",
                    "validation_logic": {
                        "check_type": "completeness",
                        "requirements": ["tables_defined", "columns_specified", "relationships_clear"]
                    },
                    "ai_validation_prompt": "Verify that this database schema is complete with all tables, columns, and relationships properly defined.",
                    "threshold_score": 0.9,
                    "severity": "high",
                    "rule_order": 1
                },
                {
                    "rule_name": "Schema Normalization",
                    "rule_type": "normalization",
                    "validation_logic": {
                        "check_type": "normalization",
                        "requirements": ["proper_normalization", "no_redundancy", "efficient_structure"]
                    },
                    "ai_validation_prompt": "Evaluate the database schema for proper normalization, lack of redundancy, and efficient structure.",
                    "threshold_score": 0.8,
                    "severity": "medium",
                    "rule_order": 2
                },
                {
                    "rule_name": "Schema Constraints",
                    "rule_type": "constraints",
                    "validation_logic": {
                        "check_type": "constraints",
                        "requirements": ["primary_keys", "foreign_keys", "data_types"]
                    },
                    "ai_validation_prompt": "Check that the schema includes proper primary keys, foreign keys, and appropriate data types with constraints.",
                    "threshold_score": 0.85,
                    "severity": "high",
                    "rule_order": 3
                }
            ],
            "test_case": [
                {
                    "rule_name": "Test Coverage",
                    "rule_type": "coverage",
                    "validation_logic": {
                        "check_type": "coverage",
                        "requirements": ["comprehensive_coverage", "edge_cases", "error_scenarios"]
                    },
                    "ai_validation_prompt": "Evaluate the test coverage including comprehensive coverage, edge cases, and error scenarios.",
                    "threshold_score": 0.8,
                    "severity": "high",
                    "rule_order": 1
                },
                {
                    "rule_name": "Test Quality",
                    "rule_type": "quality",
                    "validation_logic": {
                        "check_type": "quality",
                        "requirements": ["clear_assertions", "proper_setup", "maintainable_tests"]
                    },
                    "ai_validation_prompt": "Check the quality of test cases including clear assertions, proper setup/teardown, and maintainability.",
                    "threshold_score": 0.7,
                    "severity": "medium",
                    "rule_order": 2
                }
            ],
            "configuration": [
                {
                    "rule_name": "Configuration Completeness",
                    "rule_type": "completeness",
                    "validation_logic": {
                        "check_type": "completeness",
                        "requirements": ["all_settings_defined", "default_values", "proper_structure"]
                    },
                    "ai_validation_prompt": "Verify that this configuration is complete with all necessary settings, default values, and proper structure.",
                    "threshold_score": 0.85,
                    "severity": "high",
                    "rule_order": 1
                },
                {
                    "rule_name": "Configuration Security",
                    "rule_type": "security",
                    "validation_logic": {
                        "check_type": "security",
                        "requirements": ["no_hardcoded_secrets", "secure_defaults", "environment_variables"]
                    },
                    "ai_validation_prompt": "Check for security issues in configuration including hardcoded secrets, insecure defaults, and proper use of environment variables.",
                    "threshold_score": 0.9,
                    "severity": "high",
                    "rule_order": 2
                }
            ]
        }
    
    async def populate_all_quality_rules(self):
        """Populate the database with all quality rules"""
        logger.info("🔧 Starting quality rules population...")
        
        total_rules_created = 0
        total_rules_skipped = 0
        
        for asset_type, rules_data in self.quality_rules_definitions.items():
            logger.info(f"📋 Processing {len(rules_data)} quality rules for asset type: {asset_type}")
            
            # Check if rules already exist for this asset type
            existing_rules = await get_quality_rules(asset_type)
            if existing_rules:
                logger.info(f"⚠️ {len(existing_rules)} quality rules already exist for {asset_type}, skipping...")
                total_rules_skipped += len(existing_rules)
                continue
            
            # Create rules for this asset type
            created_count = 0
            for rule_data in rules_data:
                try:
                    # Create QualityRule instance
                    quality_rule = QualityRule(
                        id=str(uuid.uuid4()),
                        rule_name=rule_data["rule_name"],
                        rule_type=rule_data["rule_type"],
                        asset_type=asset_type,
                        validation_logic=rule_data["validation_logic"],
                        ai_validation_prompt=rule_data["ai_validation_prompt"],
                        threshold_score=rule_data["threshold_score"],
                        severity=rule_data["severity"],
                        rule_order=rule_data["rule_order"],
                        is_active=True,
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    
                    # Save to database - convert to dict and handle UUID serialization
                    rule_dict = quality_rule.dict()
                    # Convert UUID to string for database
                    if isinstance(rule_dict.get('id'), UUID):
                        rule_dict['id'] = str(rule_dict['id'])
                    
                    # Convert datetime objects to ISO strings
                    if isinstance(rule_dict.get('created_at'), datetime):
                        rule_dict['created_at'] = rule_dict['created_at'].isoformat()
                    if isinstance(rule_dict.get('updated_at'), datetime):
                        rule_dict['updated_at'] = rule_dict['updated_at'].isoformat()
                    
                    # Use direct supabase insert to avoid safe_database_operation issues
                    from database import supabase
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
                rules = await get_quality_rules(asset_type)
                verification_results[asset_type] = {
                    "count": len(rules),
                    "rules": [{"name": rule.rule_name, "type": rule.rule_type, "severity": rule.severity} for rule in rules]
                }
                logger.info(f"✅ {asset_type}: {len(rules)} rules verified")
            except Exception as e:
                logger.error(f"❌ Failed to verify rules for {asset_type}: {e}")
                verification_results[asset_type] = {"error": str(e)}
        
        return verification_results

async def main():
    """Main function to populate quality rules"""
    logger.info("🚀 Starting Quality Rules Database Population")
    
    populator = QualityRulesPopulator()
    
    try:
        # Populate quality rules
        results = await populator.populate_all_quality_rules()
        
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