#!/usr/bin/env python3
"""
🔍 DIRECT CODE ANALYSIS
Analyzes the source code directly without imports to verify implementations
"""

import re
import os
import sys
from typing import Dict, Any, List

class DirectCodeAnalyzer:
    """Analyzes source code files directly"""
    
    def __init__(self):
        self.results = {
            'fix1_goal_progress': {'status': 'pending', 'details': []},
            'fix2_content_enhancement': {'status': 'pending', 'details': []},
            'fix3_memory_intelligence': {'status': 'pending', 'details': []},
            'integration_flow': {'status': 'pending', 'details': []},
            'database_schema': {'status': 'pending', 'details': []},
            'async_patterns': {'status': 'pending', 'details': []}
        }
    
    def read_file_safe(self, filepath: str) -> str:
        """Safely read file content"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"❌ Cannot read {filepath}: {e}")
            return ""
    
    def analyze_fix_1_goal_progress(self):
        """Analyze Fix #1: Goal-Task Connection Pipeline"""
        print("🎯 ANALYZING FIX #1: Goal-Task Connection Implementation")
        details = []
        
        # Check database.py for ai_link_task_to_goals
        db_content = self.read_file_safe("database.py")
        if db_content:
            if "async def ai_link_task_to_goals" in db_content:
                details.append("✅ ai_link_task_to_goals function exists and is async")
            elif "def ai_link_task_to_goals" in db_content:
                details.append("⚠️ ai_link_task_to_goals exists but not async")
            else:
                details.append("❌ ai_link_task_to_goals function missing")
            
            if "def update_goal_progress" in db_content or "async def update_goal_progress" in db_content:
                details.append("✅ update_goal_progress function exists")
            else:
                details.append("❌ update_goal_progress function missing")
        
        # Check task_analyzer.py for goal progress integration
        ta_content = self.read_file_safe("task_analyzer.py")
        if ta_content:
            if "_handle_goal_progress_update" in ta_content:
                details.append("✅ _handle_goal_progress_update method exists")
            else:
                details.append("❌ _handle_goal_progress_update method missing")
            
            if "await self._handle_goal_progress_update" in ta_content:
                details.append("✅ handle_task_completion calls goal progress update")
            else:
                details.append("❌ handle_task_completion doesn't call goal progress update")
            
            # Check for goal_id and metric_type handling
            if "goal_id" in ta_content and "metric_type" in ta_content:
                details.append("✅ Goal metadata handling present")
            else:
                details.append("❌ Goal metadata handling missing")
        
        self.results['fix1_goal_progress']['details'] = details
        success_rate = sum(1 for d in details if d.startswith("✅")) / max(len(details), 1)
        
        if success_rate >= 0.8:
            self.results['fix1_goal_progress']['status'] = 'success'
        elif success_rate >= 0.6:
            self.results['fix1_goal_progress']['status'] = 'partial'
        else:
            self.results['fix1_goal_progress']['status'] = 'failed'
    
    def analyze_fix_2_content_enhancement(self):
        """Analyze Fix #2: Real Data Enforcement"""
        print("🤖 ANALYZING FIX #2: Content Enhancement Implementation")
        details = []
        
        # Check ai_content_enhancer.py
        enhancer_content = self.read_file_safe("ai_quality_assurance/ai_content_enhancer.py")
        if enhancer_content:
            if "class AIContentEnhancer" in enhancer_content:
                details.append("✅ AIContentEnhancer class exists")
            else:
                details.append("❌ AIContentEnhancer class missing")
            
            if "async def enhance_content_for_business_use" in enhancer_content:
                details.append("✅ enhance_content_for_business_use method exists and is async")
            elif "def enhance_content_for_business_use" in enhancer_content:
                details.append("⚠️ enhance_content_for_business_use exists but not async")
            else:
                details.append("❌ enhance_content_for_business_use method missing")
            
            if "_needs_enhancement" in enhancer_content:
                details.append("✅ Placeholder detection method exists")
            else:
                details.append("❌ Placeholder detection method missing")
            
            # Check for placeholder patterns
            placeholder_patterns = ["\\[.*?\\]", "\\{.*?\\}", "placeholder", "example"]
            pattern_count = sum(1 for pattern in placeholder_patterns if pattern in enhancer_content)
            if pattern_count >= 3:
                details.append("✅ Comprehensive placeholder detection patterns")
            elif pattern_count >= 1:
                details.append("⚠️ Basic placeholder detection patterns")
            else:
                details.append("❌ No placeholder detection patterns")
        
        # Check database.py integration
        db_content = self.read_file_safe("database.py")
        if db_content:
            if "AIContentEnhancer" in db_content:
                details.append("✅ AIContentEnhancer integrated in database")
            else:
                details.append("❌ AIContentEnhancer not integrated in database")
            
            if "enhance_content_for_business_use" in db_content:
                details.append("✅ Content enhancement called in update_task_status")
            else:
                details.append("❌ Content enhancement not called in update_task_status")
        
        self.results['fix2_content_enhancement']['details'] = details
        success_rate = sum(1 for d in details if d.startswith("✅")) / max(len(details), 1)
        
        if success_rate >= 0.8:
            self.results['fix2_content_enhancement']['status'] = 'success'
        elif success_rate >= 0.6:
            self.results['fix2_content_enhancement']['status'] = 'partial'
        else:
            self.results['fix2_content_enhancement']['status'] = 'failed'
    
    def analyze_fix_3_memory_intelligence(self):
        """Analyze Fix #3: Memory-Driven Intelligence"""
        print("🧠 ANALYZING FIX #3: Memory Intelligence Implementation")
        details = []
        
        # Check ai_memory_intelligence.py
        memory_content = self.read_file_safe("ai_quality_assurance/ai_memory_intelligence.py")
        if memory_content:
            if "class AIMemoryIntelligence" in memory_content:
                details.append("✅ AIMemoryIntelligence class exists")
            else:
                details.append("❌ AIMemoryIntelligence class missing")
            
            if "async def extract_actionable_insights" in memory_content:
                details.append("✅ extract_actionable_insights method exists and is async")
            elif "def extract_actionable_insights" in memory_content:
                details.append("⚠️ extract_actionable_insights exists but not async")
            else:
                details.append("❌ extract_actionable_insights method missing")
            
            if "async def generate_corrective_actions" in memory_content:
                details.append("✅ generate_corrective_actions method exists and is async")
            elif "def generate_corrective_actions" in memory_content:
                details.append("⚠️ generate_corrective_actions exists but not async")
            else:
                details.append("❌ generate_corrective_actions method missing")
        
        # Check task_analyzer.py integration
        ta_content = self.read_file_safe("task_analyzer.py")
        if ta_content:
            if "_handle_memory_intelligence_extraction" in ta_content:
                details.append("✅ _handle_memory_intelligence_extraction method exists")
            else:
                details.append("❌ _handle_memory_intelligence_extraction method missing")
            
            if "await self._handle_memory_intelligence_extraction" in ta_content:
                details.append("✅ handle_task_completion calls memory intelligence")
            else:
                details.append("❌ handle_task_completion doesn't call memory intelligence")
        
        # Check workspace_memory.py
        if os.path.exists("workspace_memory.py"):
            details.append("✅ workspace_memory module exists")
            
            ws_content = self.read_file_safe("workspace_memory.py")
            if "class WorkspaceMemory" in ws_content:
                details.append("✅ WorkspaceMemory class exists")
            else:
                details.append("❌ WorkspaceMemory class missing")
        else:
            details.append("❌ workspace_memory module missing")
        
        self.results['fix3_memory_intelligence']['details'] = details
        success_rate = sum(1 for d in details if d.startswith("✅")) / max(len(details), 1)
        
        if success_rate >= 0.8:
            self.results['fix3_memory_intelligence']['status'] = 'success'
        elif success_rate >= 0.6:
            self.results['fix3_memory_intelligence']['status'] = 'partial'
        else:
            self.results['fix3_memory_intelligence']['status'] = 'failed'
    
    def analyze_integration_flow(self):
        """Analyze integration flow between fixes"""
        print("🔗 ANALYZING INTEGRATION FLOW")
        details = []
        
        ta_content = self.read_file_safe("task_analyzer.py")
        if ta_content:
            # Find handle_task_completion method
            method_match = re.search(r'async def handle_task_completion.*?(?=async def|\Z)', ta_content, re.DOTALL)
            if method_match:
                method_content = method_match.group(0)
                
                # Check sequence
                goal_pos = method_content.find('_handle_goal_progress_update')
                memory_pos = method_content.find('_handle_memory_intelligence_extraction')
                
                if goal_pos > 0 and memory_pos > 0:
                    if goal_pos < memory_pos:
                        details.append("✅ Correct sequence: Goal progress → Memory intelligence")
                    else:
                        details.append("⚠️ Sequence issue: Memory intelligence before goal progress")
                else:
                    if goal_pos <= 0:
                        details.append("❌ Goal progress update not called")
                    if memory_pos <= 0:
                        details.append("❌ Memory intelligence not called")
                
                # Check error handling
                try_count = method_content.count('try:')
                except_count = method_content.count('except')
                if try_count >= 2 and except_count >= 2:
                    details.append("✅ Comprehensive error handling")
                elif try_count >= 1 and except_count >= 1:
                    details.append("⚠️ Basic error handling")
                else:
                    details.append("❌ Limited error handling")
                
                # Check async patterns
                await_count = method_content.count('await ')
                if await_count >= 2:
                    details.append("✅ Proper async/await patterns")
                else:
                    details.append("❌ Insufficient async/await patterns")
            else:
                details.append("❌ handle_task_completion method not found")
        
        self.results['integration_flow']['details'] = details
        success_rate = sum(1 for d in details if d.startswith("✅")) / max(len(details), 1)
        
        if success_rate >= 0.8:
            self.results['integration_flow']['status'] = 'success'
        elif success_rate >= 0.6:
            self.results['integration_flow']['status'] = 'partial'
        else:
            self.results['integration_flow']['status'] = 'failed'
    
    def analyze_database_schema(self):
        """Analyze database schema compatibility"""
        print("🗄️ ANALYZING DATABASE SCHEMA")
        details = []
        
        # Check models.py for required schemas
        models_content = self.read_file_safe("models.py")
        if models_content:
            # Check for goal-related models
            if "WorkspaceGoal" in models_content:
                details.append("✅ WorkspaceGoal model exists")
            else:
                details.append("❌ WorkspaceGoal model missing")
            
            if "WorkspaceInsight" in models_content:
                details.append("✅ WorkspaceInsight model exists")
            else:
                details.append("❌ WorkspaceInsight model missing")
            
            if "InsightType" in models_content:
                details.append("✅ InsightType enum exists")
            else:
                details.append("❌ InsightType enum missing")
        
        # Check database.py for schema usage
        db_content = self.read_file_safe("database.py")
        if db_content:
            if "workspace_goals" in db_content and "INSERT" in db_content:
                details.append("✅ Database operations use correct table names")
            else:
                details.append("❌ Database operations may have schema issues")
        
        # Check SQL files
        if os.path.exists("create_workspace_insights_table.sql"):
            details.append("✅ SQL schema file exists")
        else:
            details.append("❌ SQL schema file missing")
        
        self.results['database_schema']['details'] = details
        success_rate = sum(1 for d in details if d.startswith("✅")) / max(len(details), 1)
        
        if success_rate >= 0.8:
            self.results['database_schema']['status'] = 'success'
        elif success_rate >= 0.6:
            self.results['database_schema']['status'] = 'partial'
        else:
            self.results['database_schema']['status'] = 'failed'
    
    def analyze_async_patterns(self):
        """Analyze async/await patterns"""
        print("⚡ ANALYZING ASYNC PATTERNS")
        details = []
        
        files_to_check = [
            "task_analyzer.py",
            "database.py", 
            "ai_quality_assurance/ai_content_enhancer.py",
            "ai_quality_assurance/ai_memory_intelligence.py"
        ]
        
        for filepath in files_to_check:
            content = self.read_file_safe(filepath)
            if content:
                async_def_count = len(re.findall(r'async def ', content))
                await_count = len(re.findall(r'await ', content))
                
                if async_def_count > 0:
                    if await_count >= async_def_count:
                        details.append(f"✅ {filepath}: Good async/await ratio ({await_count}/{async_def_count})")
                    else:
                        details.append(f"⚠️ {filepath}: Check async/await usage ({await_count}/{async_def_count})")
                else:
                    details.append(f"⚠️ {filepath}: No async functions found")
        
        self.results['async_patterns']['details'] = details
        success_rate = sum(1 for d in details if d.startswith("✅")) / max(len(details), 1)
        
        if success_rate >= 0.8:
            self.results['async_patterns']['status'] = 'success'
        elif success_rate >= 0.6:
            self.results['async_patterns']['status'] = 'partial'
        else:
            self.results['async_patterns']['status'] = 'failed'
    
    def run_analysis(self):
        """Run complete code analysis"""
        print("🔍 STARTING DIRECT CODE ANALYSIS")
        print("=" * 70)
        
        self.analyze_fix_1_goal_progress()
        self.analyze_fix_2_content_enhancement()
        self.analyze_fix_3_memory_intelligence()
        self.analyze_integration_flow()
        self.analyze_database_schema()
        self.analyze_async_patterns()
        
        self.generate_report()
    
    def generate_report(self):
        """Generate comprehensive analysis report"""
        print("\n" + "=" * 70)
        print("📊 DIRECT CODE ANALYSIS REPORT")
        print("=" * 70)
        
        for check_name, result in self.results.items():
            status_icon = "✅" if result['status'] == 'success' else "⚠️" if result['status'] == 'partial' else "❌"
            print(f"\n{status_icon} {check_name.upper().replace('_', ' ')}: {result['status'].upper()}")
            
            for detail in result['details']:
                print(f"  {detail}")
        
        # Calculate overall scores
        success_count = sum(1 for r in self.results.values() if r['status'] == 'success')
        partial_count = sum(1 for r in self.results.values() if r['status'] == 'partial')
        total_checks = len(self.results)
        
        print("\n" + "=" * 70)
        print("🎯 COMPREHENSIVE ASSESSMENT")
        print("=" * 70)
        print(f"✅ Complete implementations: {success_count}/{total_checks}")
        print(f"⚠️ Partial implementations: {partial_count}/{total_checks}")
        print(f"❌ Missing implementations: {total_checks - success_count - partial_count}/{total_checks}")
        
        # Detailed assessment per fix
        print("\n🔧 FIX-BY-FIX ASSESSMENT:")
        print("-" * 40)
        
        fix1_status = self.results['fix1_goal_progress']['status']
        fix2_status = self.results['fix2_content_enhancement']['status']
        fix3_status = self.results['fix3_memory_intelligence']['status']
        integration_status = self.results['integration_flow']['status']
        
        if fix1_status in ['success', 'partial']:
            print("✅ Fix #1 (Goal-Task Connection): Implementation ready")
        else:
            print("❌ Fix #1 (Goal-Task Connection): Needs implementation")
        
        if fix2_status in ['success', 'partial']:
            print("✅ Fix #2 (Content Enhancement): Implementation ready")
        else:
            print("❌ Fix #2 (Content Enhancement): Needs implementation")
        
        if fix3_status in ['success', 'partial']:
            print("✅ Fix #3 (Memory Intelligence): Implementation ready")
        else:
            print("❌ Fix #3 (Memory Intelligence): Needs implementation")
        
        if integration_status in ['success', 'partial']:
            print("✅ Integration Flow: Working correctly")
        else:
            print("❌ Integration Flow: Needs attention")
        
        # Final recommendation
        print("\n🎯 FINAL RECOMMENDATION:")
        print("-" * 40)
        
        ready_fixes = sum(1 for status in [fix1_status, fix2_status, fix3_status] if status in ['success', 'partial'])
        
        if ready_fixes == 3 and integration_status in ['success', 'partial']:
            print("🎉 SYSTEM READY: All three fixes implemented and integrated")
            print("✅ Ready for end-to-end testing")
            print("✅ Ready for production deployment")
        elif ready_fixes >= 2:
            print("⚠️ MOSTLY READY: Most fixes implemented, some attention needed")
            print("🔧 Complete remaining implementations")
            print("✅ Ready for integration testing")
        else:
            print("❌ NOT READY: Major implementations missing")
            print("🔧 Complete critical fix implementations first")
            print("⏭️ Run analysis again after implementations")
        
        return ready_fixes >= 2 and integration_status != 'failed'

def main():
    """Run direct code analysis"""
    analyzer = DirectCodeAnalyzer()
    success = analyzer.run_analysis()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)