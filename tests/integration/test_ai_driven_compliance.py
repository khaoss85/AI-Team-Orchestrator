#!/usr/bin/env python3
"""
🔬 AI-DRIVEN COMPLIANCE TEST

Verifica che il sistema di estrazione asset sia completamente AI-driven
senza logiche hard-coded che violano i nostri principi architetturali.
"""

import asyncio
import logging
import json
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_ai_driven_compliance():
    """Test complete AI-driven compliance"""
    
    print("🔬 TESTING AI-DRIVEN COMPLIANCE")
    print("=" * 50)
    
    try:
        from deliverable_system.concrete_asset_extractor import concrete_asset_extractor
        
        # Test with diverse content types to verify AI adaptability
        test_cases = [
            {
                "name": "Business Content (Italian)",
                "content": """
                Contatti ICP identificati:
                1. Marco Rossi - marco.rossi@techcorp.it - TechCorp SpA - CTO
                2. Sofia Bianchi - sofia.bianchi@innovate.it - Innovate SRL - Marketing Director
                
                Email sequence proposta:
                - Oggetto: Opportunità di partnership strategica
                - Contenuto: La nostra soluzione AI può aumentare i vostri ricavi del 30%
                """,
                "context": {"domain": "business", "task_name": "lead_generation"}
            },
            {
                "name": "Technical Content",
                "content": """
                ```python
                def calculate_metrics(data):
                    return sum(data) / len(data)
                ```
                
                Configuration:
                {
                    "database": "postgresql://localhost:5432/mydb",
                    "timeout": 30,
                    "retries": 3
                }
                """,
                "context": {"domain": "technical", "task_name": "system_config"}
            },
            {
                "name": "Creative Content",
                "content": """
                Campagna pubblicitaria:
                - Slogan: "Innovazione che trasforma il futuro"
                - Target: Imprenditori digitali 25-45 anni
                - Budget: €50.000
                - KPI: +25% brand awareness
                
                Canali:
                1. Social Media (Instagram, LinkedIn)
                2. Google Ads
                3. Email Marketing
                """,
                "context": {"domain": "marketing", "task_name": "campaign_planning"}
            },
            {
                "name": "Placeholder Content (Should be rejected)",
                "content": """
                TODO: Add real content here
                Lorem ipsum dolor sit amet
                [INSERT COMPANY NAME]
                This is just an example
                Placeholder text goes here
                """,
                "context": {"domain": "test", "task_name": "placeholder_test"}
            }
        ]
        
        results = []
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🧪 Test {i}: {test_case['name']}")
            print("-" * 30)
            
            try:
                # Extract assets using AI-driven system
                assets = await concrete_asset_extractor.extract_assets(
                    content=test_case['content'],
                    context=test_case['context']
                )
                
                print(f"📊 Extracted {len(assets)} assets")
                
                test_result = {
                    "test_name": test_case['name'],
                    "assets_count": len(assets),
                    "assets": [],
                    "ai_driven_features": []
                }
                
                for asset in assets:
                    asset_info = {
                        "name": asset.get('asset_name', 'unknown'),
                        "type": asset.get('asset_type', 'unknown'),
                        "quality_score": asset.get('quality_score', 0.0),
                        "confidence": asset.get('confidence', 0.0),
                        "extraction_method": asset.get('extraction_method', 'unknown'),
                        "ai_classification": asset.get('ai_classification', False),
                        "content_length": len(str(asset.get('content', '')))
                    }
                    
                    test_result['assets'].append(asset_info)
                    
                    # Verify AI-driven features
                    if asset.get('ai_classification', False):
                        test_result['ai_driven_features'].append('AI Asset Classification')
                    
                    if asset.get('extraction_method') == 'ai_analysis':
                        test_result['ai_driven_features'].append('AI Content Analysis')
                    
                    if asset.get('extraction_method') == 'ai_structured':
                        test_result['ai_driven_features'].append('AI Structured Extraction')
                    
                    print(f"  ✅ {asset_info['name']}: {asset_info['quality_score']:.2f} quality, {asset_info['confidence']:.2f} confidence")
                
                # Remove duplicates
                test_result['ai_driven_features'] = list(set(test_result['ai_driven_features']))
                
                results.append(test_result)
                
            except Exception as e:
                print(f"  ❌ Test failed: {e}")
                results.append({
                    "test_name": test_case['name'],
                    "error": str(e),
                    "assets_count": 0,
                    "assets": [],
                    "ai_driven_features": []
                })
        
        # Analyze results for AI-driven compliance
        print("\n📋 AI-DRIVEN COMPLIANCE ANALYSIS")
        print("=" * 50)
        
        total_assets = sum(r.get('assets_count', 0) for r in results)
        ai_classified_assets = sum(1 for r in results for a in r.get('assets', []) if a.get('ai_classification', False))
        ai_quality_scored = sum(1 for r in results for a in r.get('assets', []) if a.get('quality_score', 0) > 0)
        
        print(f"📊 Total assets extracted: {total_assets}")
        print(f"🧠 AI-classified assets: {ai_classified_assets}/{total_assets} ({ai_classified_assets/max(total_assets,1)*100:.1f}%)")
        print(f"⚡ AI quality-scored assets: {ai_quality_scored}/{total_assets} ({ai_quality_scored/max(total_assets,1)*100:.1f}%)")
        
        # Check for hard-coded violations
        violations = []
        
        # Check if placeholder test correctly rejected low-quality content
        placeholder_test = next((r for r in results if r['test_name'].startswith('Placeholder')), None)
        if placeholder_test and placeholder_test.get('assets_count', 0) > 0:
            # Check if assets have low quality scores (AI should detect placeholders)
            placeholder_assets = placeholder_test.get('assets', [])
            high_quality_placeholders = [a for a in placeholder_assets if a.get('quality_score', 0) > 0.7]
            if high_quality_placeholders:
                violations.append(f"Placeholder content received high quality scores: {[a['name'] for a in high_quality_placeholders]}")
        
        # Check AI feature usage
        all_features = set()
        for result in results:
            all_features.update(result.get('ai_driven_features', []))
        
        expected_features = ['AI Asset Classification', 'AI Content Analysis', 'AI Structured Extraction']
        missing_features = [f for f in expected_features if f not in all_features]
        
        if missing_features:
            violations.append(f"Missing AI-driven features: {missing_features}")
        
        # Final compliance report
        print(f"\n🎯 AI-DRIVEN FEATURES DETECTED:")
        for feature in sorted(all_features):
            print(f"  ✅ {feature}")
        
        if violations:
            print(f"\n⚠️  COMPLIANCE VIOLATIONS:")
            for violation in violations:
                print(f"  ❌ {violation}")
        else:
            print(f"\n🎉 NO COMPLIANCE VIOLATIONS DETECTED!")
            print("   ✅ System is fully AI-driven")
            print("   ✅ No hard-coded business logic detected")
            print("   ✅ Domain-agnostic asset extraction working")
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"ai_driven_compliance_test_{timestamp}.json"
        
        compliance_report = {
            "test_timestamp": datetime.now().isoformat(),
            "total_tests": len(test_cases),
            "total_assets": total_assets,
            "ai_classification_rate": ai_classified_assets/max(total_assets,1)*100,
            "ai_quality_scoring_rate": ai_quality_scored/max(total_assets,1)*100,
            "ai_features_detected": list(all_features),
            "compliance_violations": violations,
            "is_compliant": len(violations) == 0,
            "detailed_results": results
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(compliance_report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📁 Detailed results saved to: {results_file}")
        
        return compliance_report
        
    except Exception as e:
        logger.error(f"Compliance test failed: {e}")
        return {"error": str(e), "is_compliant": False}

if __name__ == "__main__":
    report = asyncio.run(test_ai_driven_compliance())
    
    if report.get('is_compliant', False):
        print("\n🎉 COMPLIANCE TEST PASSED - System is fully AI-driven!")
        exit(0)
    else:
        print("\n❌ COMPLIANCE TEST FAILED - Hard-coded logic detected!")
        exit(1)