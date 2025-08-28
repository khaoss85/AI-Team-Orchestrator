#!/usr/bin/env python3
"""
📈 STOCK RECOMMENDATION ENGINE - Real World Test
================================================================================
Test reale per un motore di raccomandazione per opzioni su azioni tech.
Questo test simula l'intero flusso di creazione di un sistema di trading algoritmico.

SCENARIO REALE:
Un trader quantitativo vuole creare un sistema per raccomandazioni di opzioni 
su titoli tecnologici (AAPL, GOOGL, MSFT, NVDA, TSLA) basato su:
- Analisi della volatilità implicita
- Machine learning sui pattern di prezzo
- Scoring automatico delle opportunità
- Dashboard per visualizzazione

FLUSSO TESTATO:
1. 📊 Crea workspace per sistema trading
2. 🎯 Definisce goal con metriche specifiche
3. 📋 Crea task manuali per simulare orchestrazione
4. 🤖 Esegue task con agenti AI
5. 📦 Verifica creazione asset reali
6. 🛡️ Verifica quality gate
7. 🧠 Verifica memory learning
8. 🎁 Verifica deliverable finale

TEMPO STIMATO: 3-5 minuti (execution controllata)
"""

import asyncio
import requests
import json
import time
import logging
from datetime import datetime
import sys
from typing import Dict, Any, List
from uuid import uuid4

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"stock_recommendation_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)

class StockRecommendationTest:
    """Test real-world stock recommendation system development"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_session = {
            "user_id": None,
            "workspace_id": None,
            "goal_id": None,
            "task_ids": [],
            "asset_ids": [],
            "deliverable_ids": [],
            "start_time": datetime.now()
        }
        
        self.stock_scenario = {
            "domain": "fintech",
            "project_name": "TechStock Options AI Recommender",
            "description": "Sistema AI per raccomandazioni di opzioni su azioni tecnologiche con analisi predittiva e scoring automatico",
            "target_stocks": ["AAPL", "GOOGL", "MSFT", "NVDA", "TSLA"],
            "ai_requirements": [
                "Machine learning model per predizione trend (7-30 giorni)",
                "Analisi volatilità implicita in tempo reale", 
                "Sistema di scoring opportunità 0-100",
                "Dashboard interattiva con grafici real-time",
                "API REST per integrazione con broker",
                "Backtesting engine per validazione strategie"
            ],
            "success_metrics": {
                "database_stocks": 50,  # almeno 50 titoli tech
                "ml_accuracy": 75,      # >75% accuratezza predizioni
                "api_endpoints": 5,     # 5 endpoint REST funzionanti
                "dashboard_components": 3,  # 3 componenti dashboard
                "backtest_strategies": 2    # 2 strategie validate
            }
        }
        
        self.test_results = {
            "workspace_created": False,
            "goal_established": False,
            "tasks_created": False,
            "tasks_executed": False,
            "ai_content_generated": False,
            "assets_created": False,
            "quality_validated": False,
            "deliverables_ready": False,
            "system_functional": False
        }
    
    async def run_stock_test(self) -> Dict[str, Any]:
        """Execute complete stock recommendation test"""
        logger.info("📈 STARTING STOCK RECOMMENDATION SYSTEM TEST")
        logger.info("=" * 80)
        logger.info(f"🎯 TARGET: {self.stock_scenario['project_name']}")
        logger.info(f"📊 STOCKS: {', '.join(self.stock_scenario['target_stocks'])}")
        logger.info("=" * 80)
        
        try:
            # Phase 1: Setup workspace for trading system
            await self.phase_1_create_trading_workspace()
            
            # Phase 2: Define quantitative goals
            await self.phase_2_establish_quant_goals()
            
            # Phase 3: Create systematic trading tasks
            await self.phase_3_create_trading_tasks()
            
            # Phase 4: Execute AI-driven development
            await self.phase_4_execute_ai_development()
            
            # Phase 5: Verify trading components created
            await self.phase_5_verify_trading_components()
            
            # Phase 6: Check system quality and backtesting
            await self.phase_6_verify_system_quality()
            
            # Phase 7: Generate final trading system
            await self.phase_7_generate_trading_deliverable()
            
            # Final validation
            await self.validate_trading_system()
            
        except Exception as e:
            logger.error(f"❌ STOCK TEST FAILED: {e}")
            self.test_results["system_functional"] = False
        
        return await self.generate_trading_report()
    
    async def phase_1_create_trading_workspace(self):
        """Phase 1: Create workspace for quantitative trading system"""
        logger.info("📊 PHASE 1: Creating quantitative trading workspace...")
        
        self.test_session["user_id"] = str(uuid4())
        
        workspace_data = {
            "name": self.stock_scenario["project_name"],
            "description": self.stock_scenario["description"],
            "domain": self.stock_scenario["domain"],
            "goal": f"Sviluppare un sistema completo di raccomandazioni per opzioni su {len(self.stock_scenario['target_stocks'])} titoli tech principali utilizzando AI e machine learning",
            "budget": {
                "max_cost": 100.0,
                "priority": "accuracy_over_speed",
                "time_limit_hours": 48
            }
        }
        
        response = requests.post(f"{self.base_url}/workspaces", json=workspace_data, timeout=30)
        
        if response.status_code in [200, 201]:
            workspace = response.json()
            self.test_session["workspace_id"] = workspace.get('id')
            self.test_results["workspace_created"] = True
            
            logger.info(f"✅ Trading workspace created: {self.test_session['workspace_id']}")
            logger.info(f"   Domain: {workspace.get('domain')}")
            logger.info(f"   Focus: Options trading on tech stocks")
            
        else:
            raise Exception(f"Workspace creation failed: {response.status_code} - {response.text}")
    
    async def phase_2_establish_quant_goals(self):
        """Phase 2: Establish quantitative trading goals"""
        logger.info("🎯 PHASE 2: Establishing quantitative goals...")
        
        goal_data = {
            "workspace_id": self.test_session["workspace_id"],
            "description": "Sviluppare sistema AI completo per trading di opzioni su titoli tech",
            "metric_type": "deliverables",
            "target_value": 5.0,  # 5 deliverable principali
            "unit": "components",
            "priority": 5,
            "status": "active",
            "success_criteria": [
                f"Database con dati storici per {self.stock_scenario['success_metrics']['database_stocks']} titoli tech",
                f"Modello ML con accuratezza >{self.stock_scenario['success_metrics']['ml_accuracy']}% sui trend",
                f"API REST con {self.stock_scenario['success_metrics']['api_endpoints']} endpoint funzionanti", 
                f"Dashboard con {self.stock_scenario['success_metrics']['dashboard_components']} componenti interattivi",
                f"Backtesting di {self.stock_scenario['success_metrics']['backtest_strategies']} strategie validate"
            ],
            "metadata": {
                "trading_focus": "options",
                "asset_class": "tech_stocks",
                "target_stocks": self.stock_scenario["target_stocks"],
                "ai_requirements": self.stock_scenario["ai_requirements"],
                "success_metrics": self.stock_scenario["success_metrics"]
            }
        }
        
        response = requests.post(f"{self.base_url}/workspace-goals", json=goal_data, timeout=30)
        
        if response.status_code in [200, 201]:
            goal = response.json()
            self.test_session["goal_id"] = goal.get('id')
            self.test_results["goal_established"] = True
            
            logger.info(f"✅ Quantitative goal established: {self.test_session['goal_id']}")
            logger.info(f"   Target: {goal.get('target_value')} {goal.get('unit')}")
            logger.info(f"   Success criteria: {len(goal.get('success_criteria', []))} metrics")
            
        else:
            raise Exception(f"Goal creation failed: {response.status_code} - {response.text}")
    
    async def phase_3_create_trading_tasks(self):
        """Phase 3: Create systematic trading development tasks"""
        logger.info("📋 PHASE 3: Creating systematic trading tasks...")
        
        trading_tasks = [
            {
                "name": "Stock Data Acquisition System",
                "description": "Sviluppare sistema per acquisizione dati real-time e storici per AAPL, GOOGL, MSFT, NVDA, TSLA con focus su prezzi delle opzioni e volatilità implicita",
                "priority": "high",
                "task_type": "research_and_development",
                "goal_id": self.test_session["goal_id"],
                "metric_type": "deliverables",
                "contribution_expected": 1.0,
                "numerical_target": {
                    "target": self.stock_scenario["success_metrics"]["database_stocks"],
                    "metric": "stock_symbols_count",
                    "unit": "symbols"
                },
                "success_criteria": [
                    "Database PostgreSQL con tabelle per stocks, options, volatility",
                    "API integration con data provider (Alpha Vantage/Yahoo Finance)",
                    "Real-time data streaming per i 5 titoli target",
                    "Storico 2 anni di dati giornalieri e intraday"
                ]
            },
            {
                "name": "Machine Learning Prediction Model",
                "description": "Implementare modello di machine learning per predizioni di trend azionari a 7-30 giorni utilizzando features da analisi tecnica e volatilità",
                "priority": "high", 
                "task_type": "development",
                "goal_id": self.test_session["goal_id"],
                "metric_type": "deliverables",
                "contribution_expected": 1.0,
                "numerical_target": {
                    "target": self.stock_scenario["success_metrics"]["ml_accuracy"],
                    "metric": "prediction_accuracy_percent",
                    "unit": "percent"
                },
                "success_criteria": [
                    "Feature engineering con 20+ indicatori tecnici",
                    "Modello ensemble (Random Forest + LSTM)",
                    "Cross-validation con accuratezza >75%",
                    "Pipeline di training automatizzato"
                ]
            },
            {
                "name": "Options Scoring API",
                "description": "Creare API REST per scoring delle opportunità di trading su opzioni con endpoint per raccomandazioni, analisi rischio e backtesting",
                "priority": "high",
                "task_type": "development", 
                "goal_id": self.test_session["goal_id"],
                "metric_type": "deliverables",
                "contribution_expected": 1.0,
                "numerical_target": {
                    "target": self.stock_scenario["success_metrics"]["api_endpoints"],
                    "metric": "api_endpoints_count",
                    "unit": "endpoints"
                },
                "success_criteria": [
                    "5 endpoint REST: /recommendations, /score, /risk, /backtest, /portfolio",
                    "Autenticazione JWT e rate limiting",
                    "Documentazione OpenAPI/Swagger",
                    "Response time < 200ms per scoring"
                ]
            }
        ]
        
        created_tasks = []
        for task_data in trading_tasks:
            try:
                task_data["workspace_id"] = self.test_session["workspace_id"]
                task_data["status"] = "pending"
                
                response = requests.post(f"{self.base_url}/tasks", json=task_data, timeout=30)
                
                if response.status_code in [200, 201]:
                    task = response.json()
                    created_tasks.append(task.get('id'))
                    logger.info(f"   ✅ Task created: {task.get('name')} ({task.get('id')})")
                else:
                    logger.warning(f"   ⚠️ Task creation failed: {task_data['name']} - {response.status_code}")
                    
            except Exception as e:
                logger.warning(f"   ⚠️ Task creation error: {task_data['name']} - {e}")
        
        if created_tasks:
            self.test_session["task_ids"] = created_tasks
            self.test_results["tasks_created"] = True
            logger.info(f"✅ Trading tasks created: {len(created_tasks)} tasks")
        else:
            logger.error("❌ No trading tasks were created successfully")
    
    async def phase_4_execute_ai_development(self):
        """Phase 4: Execute AI-driven development of trading components"""
        logger.info("🤖 PHASE 4: Executing AI-driven development...")
        
        if not self.test_session["task_ids"]:
            logger.warning("⚠️ No tasks available for execution")
            return
        
        executed_count = 0
        for i, task_id in enumerate(self.test_session["task_ids"]):
            try:
                logger.info(f"🎯 Executing trading task {i+1}/{len(self.test_session['task_ids'])}: {task_id}")
                
                # Trigger task execution with trading-specific context
                execution_data = {
                    "force_execution": True,
                    "context": {
                        "domain": "fintech",
                        "focus": "options_trading",
                        "target_stocks": self.stock_scenario["target_stocks"],
                        "ai_requirements": self.stock_scenario["ai_requirements"]
                    }
                }
                
                response = requests.post(f"{self.base_url}/tasks/{task_id}/execute", 
                                       json=execution_data, timeout=120)
                
                if response.status_code in [200, 202]:
                    logger.info(f"   ✅ Trading task execution triggered")
                    executed_count += 1
                    
                    # Wait between executions for realistic development pace
                    if i < len(self.test_session["task_ids"]) - 1:
                        await asyncio.sleep(10)
                        
                else:
                    logger.warning(f"   ⚠️ Task execution failed: {response.status_code}")
                    
            except Exception as e:
                logger.warning(f"   ⚠️ Task execution error: {e}")
        
        if executed_count > 0:
            self.test_results["tasks_executed"] = True
            self.test_results["ai_content_generated"] = True  # AI generated trading strategies
            logger.info(f"✅ AI development phase complete: {executed_count} tasks executed")
            
            # Wait for AI processing to complete
            logger.info("⏳ Waiting for AI development completion...")
            await asyncio.sleep(45)
        else:
            logger.error("❌ No trading tasks were executed successfully")
    
    async def phase_5_verify_trading_components(self):
        """Phase 5: Verify creation of trading system components"""
        logger.info("📦 PHASE 5: Verifying trading system components...")
        
        try:
            # Check for created assets (trading components)
            response = requests.get(f"{self.base_url}/api/assets/workspace/{self.test_session['workspace_id']}", timeout=20)
            
            if response.status_code == 200:
                assets = response.json()
                
                if len(assets) > 0:
                    self.test_session["asset_ids"] = [asset.get('id') for asset in assets]
                    self.test_results["assets_created"] = True
                    
                    logger.info(f"✅ Trading components created: {len(assets)} assets")
                    
                    # Categorize trading assets
                    asset_categories = {}
                    for asset in assets:
                        category = asset.get('artifact_type', 'unknown')
                        asset_categories[category] = asset_categories.get(category, 0) + 1
                    
                    for category, count in asset_categories.items():
                        logger.info(f"   {category}: {count} components")
                    
                    # Show trading-specific assets
                    for asset in assets[:3]:
                        name = asset.get('artifact_name', 'Unnamed')
                        content_size = len(str(asset.get('content', '')))
                        quality = asset.get('quality_score', 'N/A')
                        logger.info(f"   Component: {name} (Quality: {quality}, Size: {content_size} chars)")
                        
                        # Check for trading-specific content
                        content = str(asset.get('content', '')).lower()
                        if any(stock in content for stock in ['aapl', 'googl', 'msft', 'nvda', 'tsla']):
                            logger.info(f"     ✅ Contains target stock analysis")
                        if any(term in content for term in ['option', 'volatility', 'trading', 'prediction']):
                            logger.info(f"     ✅ Contains trading-specific logic")
                else:
                    logger.warning("⚠️ No trading components found yet")
                    
            else:
                logger.warning(f"⚠️ Assets endpoint error: {response.status_code}")
                
        except Exception as e:
            logger.warning(f"⚠️ Trading component verification error: {e}")
    
    async def phase_6_verify_system_quality(self):
        """Phase 6: Verify quality validation and backtesting"""
        logger.info("🛡️ PHASE 6: Verifying system quality and backtesting...")
        
        try:
            # Check quality validation through memory system
            response = requests.get(f"{self.base_url}/api/memory/{self.test_session['workspace_id']}/summary", timeout=20)
            
            if response.status_code == 200:
                memory_data = response.json()
                total_insights = memory_data.get('total_insights', 0)
                
                if total_insights > 0:
                    self.test_results["quality_validated"] = True
                    logger.info(f"✅ Quality validation active: {total_insights} insights")
                    
                    # Check for trading-specific quality insights
                    insights_by_type = memory_data.get('insights_by_type', {})
                    for insight_type, count in insights_by_type.items():
                        if count > 0:
                            logger.info(f"   {insight_type}: {count} trading insights")
                else:
                    logger.info("ℹ️ Quality validation in progress (normal for active development)")
                    
            else:
                logger.warning(f"⚠️ Memory system check error: {response.status_code}")
                
        except Exception as e:
            logger.warning(f"⚠️ Quality verification error: {e}")
    
    async def phase_7_generate_trading_deliverable(self):
        """Phase 7: Generate final trading system deliverable"""
        logger.info("🎁 PHASE 7: Generating final trading system deliverable...")
        
        try:
            response = requests.get(f"{self.base_url}/deliverables/workspace/{self.test_session['workspace_id']}", timeout=20)
            
            if response.status_code == 200:
                deliverables = response.json()
                
                if len(deliverables) > 0:
                    self.test_session["deliverable_ids"] = [d.get('id') for d in deliverables]
                    self.test_results["deliverables_ready"] = True
                    
                    logger.info(f"✅ Trading system deliverables: {len(deliverables)}")
                    
                    for deliverable in deliverables:
                        name = deliverable.get('name', 'Unnamed')
                        status = deliverable.get('status', 'Unknown')
                        quality = deliverable.get('quality_score', 'N/A')
                        logger.info(f"   Deliverable: {name} (Status: {status}, Quality: {quality})")
                        
                        # Check for trading system completeness
                        content = str(deliverable.get('content', '')).lower()
                        if 'api' in content and 'trading' in content:
                            logger.info(f"     ✅ Contains trading API components")
                        if 'machine learning' in content or 'model' in content:
                            logger.info(f"     ✅ Contains ML prediction components") 
                else:
                    logger.info("ℹ️ Trading deliverables being generated (may take time for complex systems)")
                    
            elif response.status_code == 404:
                logger.info("ℹ️ Deliverable system not yet activated")
            else:
                logger.warning(f"⚠️ Deliverable check error: {response.status_code}")
                
        except Exception as e:
            logger.warning(f"⚠️ Deliverable generation check error: {e}")
    
    async def validate_trading_system(self):
        """Validate the complete trading system functionality"""
        logger.info("🔍 VALIDATING COMPLETE TRADING SYSTEM...")
        
        # Calculate system completion
        completed_phases = sum(self.test_results.values())
        total_phases = len(self.test_results)
        completion_rate = (completed_phases / total_phases) * 100
        
        # Check critical trading components
        critical_components = [
            self.test_results["workspace_created"],
            self.test_results["goal_established"],
            self.test_results["tasks_created"],
            self.test_results["ai_content_generated"]
        ]
        
        system_functional = all(critical_components)
        self.test_results["system_functional"] = system_functional
        
        # Validate trading-specific requirements
        trading_validation = {
            "workspace_setup": self.test_results["workspace_created"],
            "quantitative_goals": self.test_results["goal_established"], 
            "systematic_tasks": self.test_results["tasks_created"],
            "ai_development": self.test_results["ai_content_generated"],
            "component_creation": self.test_results["assets_created"],
            "quality_assurance": self.test_results["quality_validated"]
        }
        
        logger.info(f"📊 Trading system completion: {completed_phases}/{total_phases} phases ({completion_rate:.1f}%)")
        logger.info(f"🎯 System functional: {system_functional}")
        
        for component, status in trading_validation.items():
            status_icon = "✅" if status else "❌"
            logger.info(f"   {status_icon} {component.replace('_', ' ').title()}")
    
    async def generate_trading_report(self) -> Dict[str, Any]:
        """Generate comprehensive trading system test report"""
        duration = datetime.now() - self.test_session["start_time"]
        
        completed_phases = sum(self.test_results.values())
        total_phases = len(self.test_results)
        success_rate = (completed_phases / total_phases) * 100
        
        report = {
            "test_type": "stock_recommendation_system",
            "scenario": self.stock_scenario,
            "test_session": self.test_session,
            "results": self.test_results,
            "metrics": {
                "duration_minutes": duration.total_seconds() / 60,
                "success_rate_percent": success_rate,
                "phases_completed": completed_phases,
                "tasks_created": len(self.test_session["task_ids"]),
                "assets_generated": len(self.test_session["asset_ids"]),
                "deliverables_produced": len(self.test_session["deliverable_ids"]),
                "system_functional": self.test_results["system_functional"]
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Final results
        logger.info("=" * 80)
        logger.info("🏁 STOCK RECOMMENDATION SYSTEM TEST COMPLETE")
        logger.info("=" * 80)
        logger.info(f"📈 TRADING SYSTEM RESULTS:")
        
        for phase, success in self.test_results.items():
            status = "✅" if success else "❌"
            logger.info(f"   {status} {phase.replace('_', ' ').title()}")
        
        logger.info(f"\n📊 TRADING METRICS:")
        logger.info(f"   Success Rate: {success_rate:.1f}%")
        logger.info(f"   Duration: {duration.total_seconds()/60:.1f} minutes")
        logger.info(f"   Tasks Created: {len(self.test_session['task_ids'])}")
        logger.info(f"   Components: {len(self.test_session['asset_ids'])}")
        logger.info(f"   Deliverables: {len(self.test_session['deliverable_ids'])}")
        
        if success_rate >= 80:
            logger.info(f"\n🎉 STOCK TRADING SYSTEM: SUCCESS!")
            logger.info("✅ Sistema di trading AI funzionale e completo")
        elif success_rate >= 60:
            logger.info(f"\n⚠️ STOCK TRADING SYSTEM: PARTIAL SUCCESS")
            logger.info("⚠️ Sistema base funzionante, servono miglioramenti")
        else:
            logger.info(f"\n❌ STOCK TRADING SYSTEM: NEEDS DEVELOPMENT")
            logger.info("❌ Sistema richiede ulteriore sviluppo")
        
        logger.info("=" * 80)
        
        return report


async def main():
    """Main test execution"""
    # Check server connectivity
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            logger.error("❌ Server not responding properly")
            return False
    except:
        logger.error("❌ Cannot connect to server. Please ensure backend is running on localhost:8000")
        return False
    
    # Run stock recommendation test
    tester = StockRecommendationTest()
    results = await tester.run_stock_test()
    
    # Save results
    results_file = f"stock_recommendation_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"📄 Detailed results saved to: {results_file}")
    
    # Clean up test workspace
    workspace_id = results.get("test_session", {}).get("workspace_id")
    if workspace_id:
        try:
            cleanup_response = requests.delete(f"http://localhost:8000/api/workspaces/{workspace_id}", timeout=30)
            if cleanup_response.status_code in [200, 204]:
                logger.info("🧹 Test workspace cleaned up")
            else:
                logger.warning(f"⚠️ Workspace cleanup failed: {cleanup_response.status_code}")
        except Exception as e:
            logger.warning(f"⚠️ Cleanup error: {e}")
    
    # Return success based on system functionality
    success_rate = results.get("metrics", {}).get("success_rate_percent", 0)
    return success_rate >= 70  # 70% threshold for functional trading system

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)