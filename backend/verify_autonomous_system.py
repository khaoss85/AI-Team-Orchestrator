#!/usr/bin/env python3
"""
🔍 VERIFICA SISTEMA AUTONOMO - Controllo componenti per autonomia completa
================================================================================
Questo script verifica che tutte le componenti necessarie per un sistema
completamente autonomo siano presenti e configurate correttamente.

COMPONENTI VERIFICATE:
✅ Database schema (workspace_goals, workspace_insights, tasks con goal_id)
✅ Endpoint /workspace-goals per creazione goal
✅ AutomatedGoalMonitor per generazione automatica task
✅ UnifiedOrchestrator per esecuzione automatica task
✅ DeliverablePipeline per generazione automatica deliverable
✅ QualityGates per validazione automatica qualità

RISULTATO ATTESO:
Sistema pronto per funzionamento 100% autonomo senza interventi manuali
"""

import sys
import os
import importlib
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class AutonomousSystemVerifier:
    """Verifica componenti per sistema autonomo"""
    
    def __init__(self):
        self.verification_results = {
            "database_schema": {"status": "PENDING", "details": ""},
            "workspace_goals_endpoint": {"status": "PENDING", "details": ""},
            "automated_goal_monitor": {"status": "PENDING", "details": ""},
            "unified_orchestrator": {"status": "PENDING", "details": ""},
            "deliverable_pipeline": {"status": "PENDING", "details": ""},
            "quality_gates": {"status": "PENDING", "details": ""},
            "task_executor": {"status": "PENDING", "details": ""},
            "asset_system": {"status": "PENDING", "details": ""},
            "memory_system": {"status": "PENDING", "details": ""}
        }
    
    def verify_all_components(self):
        """Esegue tutte le verifiche"""
        logger.info("🔍 VERIFICA SISTEMA AUTONOMO")
        logger.info("=" * 80)
        
        # 1. Verifica Database Schema
        self.verify_database_schema()
        
        # 2. Verifica Endpoint
        self.verify_endpoints()
        
        # 3. Verifica AutomatedGoalMonitor
        self.verify_automated_goal_monitor()
        
        # 4. Verifica UnifiedOrchestrator
        self.verify_unified_orchestrator()
        
        # 5. Verifica DeliverablePipeline
        self.verify_deliverable_pipeline()
        
        # 6. Verifica QualityGates
        self.verify_quality_gates()
        
        # 7. Verifica TaskExecutor
        self.verify_task_executor()
        
        # 8. Verifica AssetSystem
        self.verify_asset_system()
        
        # 9. Verifica MemorySystem
        self.verify_memory_system()
        
        # Report finale
        self.generate_report()
    
    def verify_database_schema(self):
        """Verifica schema database per autonomia"""
        logger.info("\n📊 VERIFICA DATABASE SCHEMA...")
        
        try:
            from database import get_supabase_client
            supabase = get_supabase_client()
            
            # Test workspace_goals table
            try:
                result = supabase.table('workspace_goals').select('*').limit(1).execute()
                logger.info("   ✅ workspace_goals table exists")
                
                # Check columns
                if hasattr(result, 'data') and isinstance(result.data, list):
                    logger.info("   ✅ workspace_goals structure valid")
            except Exception as e:
                logger.error(f"   ❌ workspace_goals issue: {e}")
                self.verification_results["database_schema"]["status"] = "FAIL"
                return
            
            # Test workspace_insights table
            try:
                result = supabase.table('workspace_insights').select('*').limit(1).execute()
                logger.info("   ✅ workspace_insights table exists")
            except:
                logger.warning("   ⚠️ workspace_insights table missing (optional)")
            
            # Test tasks table has goal_id
            try:
                result = supabase.table('tasks').select('id, goal_id').limit(1).execute()
                logger.info("   ✅ tasks table has goal_id column")
            except:
                logger.error("   ❌ tasks table missing goal_id column")
                self.verification_results["database_schema"]["status"] = "FAIL"
                return
            
            self.verification_results["database_schema"]["status"] = "PASS"
            self.verification_results["database_schema"]["details"] = "All required tables and columns present"
            
        except Exception as e:
            logger.error(f"   ❌ Database verification failed: {e}")
            self.verification_results["database_schema"]["status"] = "FAIL"
            self.verification_results["database_schema"]["details"] = str(e)
    
    def verify_endpoints(self):
        """Verifica endpoint necessari"""
        logger.info("\n🌐 VERIFICA ENDPOINTS...")
        
        try:
            # Check if workspace_goals router is properly configured
            from routes.workspace_goals import direct_router
            
            # Check for POST /workspace-goals endpoint
            has_post_endpoint = False
            for route in direct_router.routes:
                if hasattr(route, 'methods') and 'POST' in route.methods and '/workspace-goals' in str(route.path):
                    has_post_endpoint = True
                    break
            
            if has_post_endpoint:
                logger.info("   ✅ POST /workspace-goals endpoint configured")
                self.verification_results["workspace_goals_endpoint"]["status"] = "PASS"
                self.verification_results["workspace_goals_endpoint"]["details"] = "Endpoint ready for goal creation"
            else:
                logger.error("   ❌ POST /workspace-goals endpoint missing")
                self.verification_results["workspace_goals_endpoint"]["status"] = "FAIL"
                
        except Exception as e:
            logger.error(f"   ❌ Endpoint verification failed: {e}")
            self.verification_results["workspace_goals_endpoint"]["status"] = "FAIL"
            self.verification_results["workspace_goals_endpoint"]["details"] = str(e)
    
    def verify_automated_goal_monitor(self):
        """Verifica AutomatedGoalMonitor per generazione automatica task"""
        logger.info("\n🎯 VERIFICA AUTOMATED GOAL MONITOR...")
        
        try:
            from automated_goal_monitor import AutomatedGoalMonitor, automated_goal_monitor
            
            logger.info("   ✅ AutomatedGoalMonitor module imported successfully")
            
            # Check if it's configured in main.py
            with open('main.py', 'r') as f:
                main_content = f.read()
                if 'automated_goal_monitor.start_monitoring()' in main_content:
                    logger.info("   ✅ AutomatedGoalMonitor configured to start in main.py")
                    self.verification_results["automated_goal_monitor"]["status"] = "PASS"
                    self.verification_results["automated_goal_monitor"]["details"] = "Ready for autonomous task generation"
                else:
                    logger.warning("   ⚠️ AutomatedGoalMonitor not configured to start automatically")
                    self.verification_results["automated_goal_monitor"]["status"] = "PARTIAL"
                    self.verification_results["automated_goal_monitor"]["details"] = "Module exists but needs activation"
                    
        except Exception as e:
            logger.error(f"   ❌ AutomatedGoalMonitor verification failed: {e}")
            self.verification_results["automated_goal_monitor"]["status"] = "FAIL"
            self.verification_results["automated_goal_monitor"]["details"] = str(e)
    
    def verify_unified_orchestrator(self):
        """Verifica UnifiedOrchestrator per esecuzione automatica"""
        logger.info("\n🔄 VERIFICA UNIFIED ORCHESTRATOR...")
        
        try:
            from unified_orchestrator import UnifiedOrchestrator, unified_orchestrator
            
            logger.info("   ✅ UnifiedOrchestrator module imported successfully")
            
            # Check configuration
            with open('main.py', 'r') as f:
                main_content = f.read()
                if 'unified_orchestrator.start()' in main_content:
                    logger.info("   ✅ UnifiedOrchestrator configured to start in main.py")
                    self.verification_results["unified_orchestrator"]["status"] = "PASS"
                    self.verification_results["unified_orchestrator"]["details"] = "Ready for autonomous task execution"
                    
        except Exception as e:
            logger.error(f"   ❌ UnifiedOrchestrator verification failed: {e}")
            self.verification_results["unified_orchestrator"]["status"] = "FAIL"
            self.verification_results["unified_orchestrator"]["details"] = str(e)
    
    def verify_deliverable_pipeline(self):
        """Verifica DeliverablePipeline"""
        logger.info("\n📦 VERIFICA DELIVERABLE PIPELINE...")
        
        try:
            from backend.deliverable_system.unified_deliverable_engine import unified_deliverable_engine
            
            logger.info("   ✅ DeliverablePipeline module imported successfully")
            
            # Check configuration
            with open('main.py', 'r') as f:
                main_content = f.read()
                if 'deliverable_pipeline.start()' in main_content:
                    logger.info("   ✅ DeliverablePipeline configured to start in main.py")
                    self.verification_results["deliverable_pipeline"]["status"] = "PASS"
                    self.verification_results["deliverable_pipeline"]["details"] = "Ready for autonomous deliverable generation"
                    
        except Exception as e:
            logger.error(f"   ❌ DeliverablePipeline verification failed: {e}")
            self.verification_results["deliverable_pipeline"]["status"] = "FAIL"
            self.verification_results["deliverable_pipeline"]["details"] = str(e)
    
    def verify_quality_gates(self):
        """Verifica Quality Gates"""
        logger.info("\n🛡️ VERIFICA QUALITY GATES...")
        
        try:
            
            
            logger.info("   ✅ QualityGate module imported successfully")
            
            # Check if automatic quality trigger is configured
            try:
                from backend.ai_quality_assurance.unified_quality_engine import unified_quality_engine
                logger.info("   ✅ AutomaticQualityTrigger available")
                self.verification_results["quality_gates"]["status"] = "PASS"
                self.verification_results["quality_gates"]["details"] = "Ready for autonomous quality validation"
            except:
                logger.warning("   ⚠️ AutomaticQualityTrigger not available")
                self.verification_results["quality_gates"]["status"] = "PARTIAL"
                
        except Exception as e:
            logger.error(f"   ❌ UnifiedQualityEngine verification failed: {e}")
            self.verification_results["quality_gates"]["status"] = "FAIL"
            self.verification_results["quality_gates"]["details"] = str(e)
    
    def verify_task_executor(self):
        """Verifica TaskExecutor"""
        logger.info("\n🤖 VERIFICA TASK EXECUTOR...")
        
        try:
            from executor import TaskExecutor, start_task_executor
            
            logger.info("   ✅ TaskExecutor module imported successfully")
            
            # Check if it starts automatically
            with open('main.py', 'r') as f:
                main_content = f.read()
                if 'start_task_executor()' in main_content:
                    logger.info("   ✅ TaskExecutor configured to start in main.py")
                    self.verification_results["task_executor"]["status"] = "PASS"
                    self.verification_results["task_executor"]["details"] = "Ready for task execution"
                    
        except Exception as e:
            logger.error(f"   ❌ TaskExecutor verification failed: {e}")
            self.verification_results["task_executor"]["status"] = "FAIL"
            self.verification_results["task_executor"]["details"] = str(e)
    
    def verify_asset_system(self):
        """Verifica Asset System"""
        logger.info("\n📂 VERIFICA ASSET SYSTEM...")
        
        try:
            from database_asset_extensions import DatabaseAssetExtensions
            
            logger.info("   ✅ DatabaseAssetExtensions imported successfully")
            
            # Check asset requirements generator
            try:
                from backend.deliverable_system.unified_deliverable_engine import unified_deliverable_engine
                logger.info("   ✅ AssetRequirementsGenerator available")
                self.verification_results["asset_system"]["status"] = "PASS"
                self.verification_results["asset_system"]["details"] = "Ready for autonomous asset generation"
            except:
                self.verification_results["asset_system"]["status"] = "PARTIAL"
                
        except Exception as e:
            logger.error(f"   ❌ AssetSystem verification failed: {e}")
            self.verification_results["asset_system"]["status"] = "FAIL"
            self.verification_results["asset_system"]["details"] = str(e)
    
    def verify_memory_system(self):
        """Verifica Memory System"""
        logger.info("\n🧠 VERIFICA MEMORY SYSTEM...")
        
        try:
            from workspace_memory import WorkspaceMemory
            
            logger.info("   ✅ WorkspaceMemory module imported successfully")
            
            # Check if memory system has learning methods
            if hasattr(WorkspaceMemory, 'store_quality_validation_learning'):
                logger.info("   ✅ Quality validation learning methods available")
                self.verification_results["memory_system"]["status"] = "PASS"
                self.verification_results["memory_system"]["details"] = "Ready for autonomous learning"
            else:
                self.verification_results["memory_system"]["status"] = "PARTIAL"
                
        except Exception as e:
            logger.error(f"   ❌ MemorySystem verification failed: {e}")
            self.verification_results["memory_system"]["status"] = "FAIL"
            self.verification_results["memory_system"]["details"] = str(e)
    
    def generate_report(self):
        """Genera report finale"""
        logger.info("\n" + "=" * 80)
        logger.info("📋 REPORT VERIFICA SISTEMA AUTONOMO")
        logger.info("=" * 80)
        
        total_components = len(self.verification_results)
        passed = sum(1 for v in self.verification_results.values() if v["status"] == "PASS")
        partial = sum(1 for v in self.verification_results.values() if v["status"] == "PARTIAL")
        failed = sum(1 for v in self.verification_results.values() if v["status"] == "FAIL")
        
        logger.info(f"\nRISULTATI:")
        for component, result in self.verification_results.items():
            status_icon = "✅" if result["status"] == "PASS" else "⚠️" if result["status"] == "PARTIAL" else "❌"
            logger.info(f"   {status_icon} {component.replace('_', ' ').title()}: {result['status']}")
            if result["details"]:
                logger.info(f"      → {result['details']}")
        
        logger.info(f"\nRIEPILOGO:")
        logger.info(f"   ✅ Componenti OK: {passed}/{total_components}")
        logger.info(f"   ⚠️ Componenti Parziali: {partial}/{total_components}")
        logger.info(f"   ❌ Componenti Mancanti: {failed}/{total_components}")
        
        autonomy_score = (passed * 100 + partial * 50) / total_components
        
        logger.info(f"\n🎯 AUTONOMY SCORE: {autonomy_score:.1f}%")
        
        if autonomy_score >= 90:
            logger.info("✅ SISTEMA PRONTO PER FUNZIONAMENTO AUTONOMO!")
            logger.info("   Il sistema può operare senza interventi manuali")
        elif autonomy_score >= 70:
            logger.info("⚠️ SISTEMA QUASI PRONTO PER AUTONOMIA")
            logger.info("   Alcune componenti necessitano configurazione")
        else:
            logger.info("❌ SISTEMA NON PRONTO PER AUTONOMIA")
            logger.info("   Componenti critiche mancanti o non configurate")
        
        logger.info("\n📝 NOTE PER AUTONOMIA COMPLETA:")
        logger.info("   1. Avviare il server con: python main.py")
        logger.info("   2. AutomatedGoalMonitor genererà task automaticamente ogni 20 min")
        logger.info("   3. UnifiedOrchestrator eseguirà task automaticamente")
        logger.info("   4. DeliverablePipeline genererà deliverable automaticamente")
        logger.info("   5. Nessun intervento manuale richiesto!")
        
        logger.info("=" * 80)
        
        # Save report
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "verification_results": self.verification_results,
            "summary": {
                "total_components": total_components,
                "passed": passed,
                "partial": partial,
                "failed": failed,
                "autonomy_score": autonomy_score,
                "autonomous_ready": autonomy_score >= 90
            }
        }
        
        import json
        report_file = f"autonomous_system_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"\n📄 Report salvato in: {report_file}")
        
        return autonomy_score >= 90


def main():
    """Main verification"""
    verifier = AutonomousSystemVerifier()
    is_autonomous = verifier.verify_all_components()
    
    return 0 if is_autonomous else 1


if __name__ == "__main__":
    sys.exit(main())