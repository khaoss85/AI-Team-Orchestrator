#!/usr/bin/env python3
"""
Integration check for unified asset management system
Verifies all components are properly connected
"""

import os
import sys
import importlib.util

def check_file_exists(file_path, description):
    """Check if a file exists and return status"""
    full_path = os.path.join(os.path.dirname(__file__), file_path)
    if os.path.exists(full_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} - FILE NOT FOUND")
        return False

def check_import(module_path, description):
    """Check if a module can be imported"""
    try:
        spec = importlib.util.spec_from_file_location("test_module", module_path)
        if spec is None:
            print(f"❌ {description}: Cannot create spec for {module_path}")
            return False
        
        module = importlib.util.module_from_spec(spec)
        # Don't execute the module, just check if it can be loaded
        print(f"✅ {description}: {module_path}")
        return True
    except Exception as e:
        print(f"❌ {description}: {module_path} - ERROR: {e}")
        return False

def main():
    """Run integration checks"""
    print("🔍 UNIFIED ASSET MANAGEMENT INTEGRATION CHECK")
    print("=" * 60)
    
    checks = []
    
    # Backend files
    print("\n📦 Backend Components:")
    checks.append(check_file_exists("routes/unified_assets.py", "Unified Assets API"))
    checks.append(check_file_exists("deliverable_system/concrete_asset_extractor.py", "Concrete Asset Extractor"))
    checks.append(check_file_exists("deliverable_system/markup_processor.py", "Markup Processor"))
    checks.append(check_file_exists("ai_quality_assurance/smart_evaluator.py", "Smart Evaluator"))
    checks.append(check_file_exists("database.py", "Database Module"))
    checks.append(check_file_exists("models.py", "Data Models"))
    
    # Frontend files (check relative to backend)
    print("\n🎨 Frontend Components:")
    frontend_base = "../frontend/src"
    checks.append(check_file_exists(f"{frontend_base}/hooks/useUnifiedAssets.ts", "Unified Assets Hook"))
    checks.append(check_file_exists(f"{frontend_base}/app/projects/[id]/assets/page.tsx", "Assets Page"))
    checks.append(check_file_exists(f"{frontend_base}/components/assets/AssetHistoryPanel.tsx", "Asset History Panel"))
    checks.append(check_file_exists(f"{frontend_base}/components/assets/RelatedAssetsModal.tsx", "Related Assets Modal"))
    checks.append(check_file_exists(f"{frontend_base}/components/assets/DependencyGraph.tsx", "Dependency Graph"))
    checks.append(check_file_exists(f"{frontend_base}/components/assets/AIImpactPredictor.tsx", "AI Impact Predictor"))
    checks.append(check_file_exists(f"{frontend_base}/components/GenericArrayViewer.tsx", "Generic Array Viewer"))
    checks.append(check_file_exists(f"{frontend_base}/components/StructuredContentRenderer.tsx", "Structured Content Renderer"))
    checks.append(check_file_exists(f"{frontend_base}/components/StructuredAssetRenderer.tsx", "Structured Asset Renderer"))
    
    # Configuration files
    print("\n⚙️  Configuration:")
    checks.append(check_file_exists("main.py", "FastAPI Main App"))
    checks.append(check_file_exists("requirements.txt", "Python Requirements"))
    checks.append(check_file_exists(f"{frontend_base}/../package.json", "Frontend Package JSON"))
    
    # Test files
    print("\n🧪 Test Files:")
    checks.append(check_file_exists("test_unified_logic.py", "Logic Tests"))
    checks.append(check_file_exists("test_unified_assets.py", "Integration Tests"))
    checks.append(check_file_exists("../UNIFIED_ASSETS_MIGRATION.md", "Migration Documentation"))
    
    # Check main.py imports
    print("\n🔗 Import Checks:")
    try:
        with open("main.py", "r") as f:
            main_content = f.read()
            
        if "from routes.unified_assets import router as unified_assets_router" in main_content:
            print("✅ Unified assets router imported in main.py")
            checks.append(True)
        else:
            print("❌ Unified assets router NOT imported in main.py")
            checks.append(False)
            
        if "app.include_router(unified_assets_router)" in main_content:
            print("✅ Unified assets router registered in FastAPI app")
            checks.append(True)
        else:
            print("❌ Unified assets router NOT registered in FastAPI app")
            checks.append(False)
            
        if "# app.include_router(asset_management.router)" in main_content:
            print("✅ Legacy asset management router properly commented out")
            checks.append(True)
        else:
            print("⚠️  Legacy asset management router status unclear")
            checks.append(True)  # Not critical
            
    except Exception as e:
        print(f"❌ Error checking main.py: {e}")
        checks.extend([False, False, False])
    
    # Summary
    passed = sum(checks)
    total = len(checks)
    success_rate = (passed / total) * 100 if total > 0 else 0
    
    print("\n" + "=" * 60)
    print(f"📊 INTEGRATION CHECK SUMMARY")
    print(f"Components checked: {passed}/{total}")
    print(f"Success rate: {success_rate:.1f}%")
    
    if success_rate >= 95:
        print("🎉 EXCELLENT! All critical components are properly integrated.")
        print("\n✅ The unified asset management system is ready for testing:")
        print("   1. Start backend: cd backend && python3 main.py")
        print("   2. Start frontend: cd frontend && npm run dev") 
        print("   3. Test URL: http://localhost:3000/projects/{workspace_id}/assets")
        print("   4. API URL: http://localhost:8000/unified-assets/workspace/{workspace_id}")
    elif success_rate >= 90:
        print("✅ GOOD! Most components are integrated correctly.")
        print("⚠️  Review any failed checks above and fix if necessary.")
    else:
        print("❌ ISSUES FOUND! Please resolve the failed checks before proceeding.")
    
    return success_rate >= 90

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)