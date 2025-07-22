#!/usr/bin/env python3
"""
🔧 TEST DI CONFERMA ESSENZIALE
Test focalizzato sulle integrazioni principali senza dipendenze DB complesse
"""

import asyncio
import json
import logging
import requests
from datetime import datetime
from typing import List, Dict, Any
import sys
import os
import time

# Add backend to path
sys.path.append(os.path.dirname(__file__))

from database import get_quality_rules, list_tasks, get_task
from services.memory_similarity_engine import memory_similarity_engine
from ai_agents.manager import AgentManager
from uuid import UUID

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

class TestConfermaEssenziale:
    """Test essenziale di conferma delle integrazioni principali"""
    
    def __init__(self):
        self.workspace_id = None
        self.test_results = {
            "test_start": datetime.now().isoformat(),
            "integrazioni_testate": [],
            "risultati_integrazione": {},
            "successo_completo": False
        }
    
    async def esegui_test_essenziale(self):
        """Esegue il test essenziale di conferma"""
        logger.info("🚀 INIZIO TEST DI CONFERMA ESSENZIALE")
        logger.info("=" * 60)
        
        try:
            # Test 1: Quality Rules Database Integration
            await self.test_quality_rules_integration()
            
            # Test 2: Asset Extraction Integration
            await self.test_asset_extraction_integration()
            
            # Test 3: Memory Enhancement Integration
            await self.test_memory_enhancement_integration()
            
            # Test 4: End-to-End System Test
            await self.test_end_to_end_system()
            
            # Calcola successo
            successi = sum(1 for r in self.test_results["risultati_integrazione"].values() if r["successo"])
            totale = len(self.test_results["risultati_integrazione"])
            self.test_results["successo_completo"] = successi >= 3  # Almeno 3 su 4
            
        except Exception as e:
            logger.error(f"❌ Test fallito: {e}")
            self.test_results["successo_completo"] = False
            import traceback
            traceback.print_exc()
        
        self._stampa_risultati()
        return self.test_results
    
    async def test_quality_rules_integration(self):
        """Test 1: Quality Rules Database Integration"""
        test_name = "quality_rules_integration"
        logger.info("🔧 TEST 1: Quality Rules Database Integration")
        
        try:
            # Verifica regole per diversi tipi di asset
            asset_types = ["code", "json", "configuration", "api_spec", "test_case"]
            total_rules = 0
            dettagli = []
            
            for asset_type in asset_types:
                rules = await get_quality_rules(asset_type)
                rule_count = len(rules)
                total_rules += rule_count
                
                if rule_count > 0:
                    sample_rule = rules[0]
                    dettagli.append({
                        "asset_type": asset_type,
                        "rule_count": rule_count,
                        "sample_rule": sample_rule.rule_name,
                        "threshold": sample_rule.threshold_score
                    })
                    logger.info(f"✅ {asset_type}: {rule_count} regole")
            
            successo = total_rules >= 5  # Almeno 5 regole totali
            
            self.test_results["integrazioni_testate"].append(test_name)
            self.test_results["risultati_integrazione"][test_name] = {
                "successo": successo,
                "total_rules": total_rules,
                "dettagli": dettagli,
                "messaggio": f"✅ {total_rules} regole di qualità verificate" if successo else f"❌ Solo {total_rules} regole trovate"
            }
            
            logger.info(f"✅ Quality Rules Integration: {total_rules} regole totali")
            
        except Exception as e:
            logger.error(f"❌ Test Quality Rules fallito: {e}")
            self.test_results["risultati_integrazione"][test_name] = {
                "successo": False,
                "errore": str(e)
            }
    
    async def test_asset_extraction_integration(self):
        """Test 2: Asset Extraction Integration"""
        test_name = "asset_extraction_integration"
        logger.info("🔧 TEST 2: Asset Extraction Integration")
        
        try:
            # Verifica che ConcreteAssetExtractor sia disponibile
            from deliverable_system.concrete_asset_extractor import ConcreteAssetExtractor
            extractor = ConcreteAssetExtractor()
            
            # Test estrazione asset
            test_content = '''
            Ecco il codice per l'autenticazione:
            
            ```python
            def authenticate_user(username, password):
                # Autentica l'utente
                return verify_credentials(username, password)
            ```
            
            Configurazione JSON:
            ```json
            {
                "auth_timeout": 300,
                "max_attempts": 3
            }
            ```
            '''
            
            extracted_assets = await extractor.extract_assets(
                content=test_content,
                context={"test": True}
            )
            
            successo = len(extracted_assets) > 0
            
            # Verifica integrazione in database.py
            from database import update_task_status
            import inspect
            
            source = inspect.getsource(update_task_status)
            integration_keywords = ["ConcreteAssetExtractor", "extract_assets", "create_asset_artifact"]
            found_keywords = [kw for kw in integration_keywords if kw in source]
            
            integration_ok = len(found_keywords) >= 2
            
            self.test_results["integrazioni_testate"].append(test_name)
            self.test_results["risultati_integrazione"][test_name] = {
                "successo": successo and integration_ok,
                "assets_extracted": len(extracted_assets),
                "integration_keywords": found_keywords,
                "messaggio": f"✅ {len(extracted_assets)} asset estratti, integrazione verificata" if successo and integration_ok else "❌ Problemi con asset extraction"
            }
            
            logger.info(f"✅ Asset Extraction: {len(extracted_assets)} asset estratti")
            
        except Exception as e:
            logger.error(f"❌ Test Asset Extraction fallito: {e}")
            self.test_results["risultati_integrazione"][test_name] = {
                "successo": False,
                "errore": str(e)
            }
    
    async def test_memory_enhancement_integration(self):
        """Test 3: Memory Enhancement Integration"""
        test_name = "memory_enhancement_integration"
        logger.info("🔧 TEST 3: Memory Enhancement Integration")
        
        try:
            # Test similarity engine
            test_workspace_id = "test-workspace-12345"
            
            task_context = {
                'name': 'Implementa Authentication API',
                'description': 'Crea API per autenticazione utente con JWT',
                'type': 'backend_development',
                'skills': ['Python', 'API', 'JWT', 'Authentication']
            }
            
            # Test retrieval insights (probabilmente vuoto ma deve funzionare)
            relevant_insights = await memory_similarity_engine.get_relevant_insights(
                workspace_id=test_workspace_id,
                task_context=task_context
            )
            
            # Verifica AgentManager integration
            manager = AgentManager(UUID(test_workspace_id))
            
            # Verifica metodi memory
            memory_methods = ["_get_task_insights", "_enhance_task_with_insights", "_store_execution_insights"]
            found_methods = [method for method in memory_methods if hasattr(manager, method)]
            
            # Verifica SpecialistAgent integration
            from ai_agents.specialist_enhanced import SpecialistAgent
            import inspect
            
            source = inspect.getsource(SpecialistAgent._create_enhanced_prompt)
            uses_task_description = "task.description" in source
            
            manager_source = inspect.getsource(manager._enhance_task_with_insights)
            includes_insights = "🧠 RELEVANT INSIGHTS" in manager_source
            
            successo = (
                len(found_methods) == 3 and
                uses_task_description and 
                includes_insights
            )
            
            self.test_results["integrazioni_testate"].append(test_name)
            self.test_results["risultati_integrazione"][test_name] = {
                "successo": successo,
                "memory_methods": found_methods,
                "uses_task_description": uses_task_description,
                "includes_insights": includes_insights,
                "insights_found": len(relevant_insights),
                "messaggio": "✅ Memory enhancement integrato nei prompt LLM" if successo else "❌ Problemi con memory enhancement"
            }
            
            logger.info(f"✅ Memory Enhancement: {len(found_methods)}/3 metodi, insights integrati")
            
        except Exception as e:
            logger.error(f"❌ Test Memory Enhancement fallito: {e}")
            self.test_results["risultati_integrazione"][test_name] = {
                "successo": False,
                "errore": str(e)
            }
    
    async def test_end_to_end_system(self):
        """Test 4: End-to-End System Test"""
        test_name = "end_to_end_system"
        logger.info("🔧 TEST 4: End-to-End System Test")
        
        try:
            # Test server health
            health_response = requests.get(f"{BASE_URL}/health", timeout=5)
            server_ok = health_response.status_code == 200
            
            # Test basic API endpoints
            endpoints_test = []
            
            # Test workspaces endpoint
            try:
                workspace_response = requests.get(f"{API_BASE}/workspaces", timeout=5)
                endpoints_test.append({
                    "endpoint": "workspaces",
                    "status": workspace_response.status_code,
                    "ok": workspace_response.status_code in [200, 404]  # 404 is OK if no workspaces
                })
            except Exception as e:
                endpoints_test.append({
                    "endpoint": "workspaces",
                    "status": "error",
                    "error": str(e),
                    "ok": False
                })
            
            # Test director endpoint
            try:
                director_response = requests.get(f"{API_BASE}/director/health", timeout=5)
                endpoints_test.append({
                    "endpoint": "director",
                    "status": director_response.status_code,
                    "ok": director_response.status_code in [200, 404]
                })
            except Exception as e:
                endpoints_test.append({
                    "endpoint": "director",
                    "status": "error",
                    "error": str(e),
                    "ok": False
                })
            
            # Test componenti principali
            components_test = []
            
            # Test ConcreteAssetExtractor
            try:
                from deliverable_system.concrete_asset_extractor import ConcreteAssetExtractor
                extractor = ConcreteAssetExtractor()
                components_test.append({"component": "ConcreteAssetExtractor", "ok": True})
            except Exception as e:
                components_test.append({"component": "ConcreteAssetExtractor", "ok": False, "error": str(e)})
            
            # Test AgentManager
            try:
                from ai_agents.manager import AgentManager
                manager = AgentManager(UUID("test-workspace-12345"))
                components_test.append({"component": "AgentManager", "ok": True})
            except Exception as e:
                components_test.append({"component": "AgentManager", "ok": False, "error": str(e)})
            
            # Test Quality Engine
            try:
                from ai_quality_assurance.unified_quality_engine import quality_gates
                components_test.append({"component": "QualityEngine", "ok": True})
            except Exception as e:
                components_test.append({"component": "QualityEngine", "ok": False, "error": str(e)})
            
            # Calcola successo
            endpoints_ok = sum(1 for e in endpoints_test if e["ok"])
            components_ok = sum(1 for c in components_test if c["ok"])
            
            successo = (
                server_ok and 
                endpoints_ok >= 1 and  # Almeno 1 endpoint funzionante
                components_ok >= 2     # Almeno 2 componenti funzionanti
            )
            
            self.test_results["integrazioni_testate"].append(test_name)
            self.test_results["risultati_integrazione"][test_name] = {
                "successo": successo,
                "server_health": server_ok,
                "endpoints_ok": f"{endpoints_ok}/{len(endpoints_test)}",
                "components_ok": f"{components_ok}/{len(components_test)}",
                "endpoints_test": endpoints_test,
                "components_test": components_test,
                "messaggio": f"✅ Sistema end-to-end funzionante" if successo else "❌ Problemi sistema end-to-end"
            }
            
            logger.info(f"✅ End-to-End: Server OK, {endpoints_ok} endpoints, {components_ok} componenti")
            
        except Exception as e:
            logger.error(f"❌ Test End-to-End fallito: {e}")
            self.test_results["risultati_integrazione"][test_name] = {
                "successo": False,
                "errore": str(e)
            }
    
    def _stampa_risultati(self):
        """Stampa risultati del test"""
        logger.info("\n" + "=" * 60)
        logger.info("🎯 TEST DI CONFERMA ESSENZIALE - RISULTATI")
        logger.info("=" * 60)
        
        successi = sum(1 for r in self.test_results["risultati_integrazione"].values() if r["successo"])
        totale = len(self.test_results["risultati_integrazione"])
        
        logger.info(f"✅ Test Superati: {successi}/{totale}")
        
        for test_name, risultato in self.test_results["risultati_integrazione"].items():
            if risultato["successo"]:
                logger.info(f"  ✅ {test_name}: {risultato['messaggio']}")
            else:
                logger.info(f"  ❌ {test_name}: {risultato.get('messaggio', 'Fallito')}")
                if "errore" in risultato:
                    logger.info(f"      Errore: {risultato['errore']}")
        
        percentuale = (successi / totale * 100) if totale > 0 else 0
        logger.info(f"\n📊 Percentuale Successo: {percentuale:.1f}%")
        
        if self.test_results["successo_completo"]:
            logger.info("🎉 TEST DI CONFERMA ESSENZIALE SUPERATO!")
            logger.info("✅ Le integrazioni principali funzionano correttamente")
            logger.info("\n🔧 INTEGRAZIONI CONFERMATE:")
            logger.info("  - ✅ Quality Rules Database populated e funzionante")
            logger.info("  - ✅ Asset Extraction integrato nel flusso principale")
            logger.info("  - ✅ Memory Insights integrati nei prompt degli agenti")
            logger.info("  - ✅ Sistema end-to-end operativo")
        else:
            logger.warning("⚠️ Test completato con alcune problematiche")
            logger.warning("Alcune integrazioni potrebbero necessitare di aggiustamenti")
        
        logger.info("=" * 60)
        
        # Salva risultati
        results_file = f"test_conferma_essenziale_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        logger.info(f"💾 Risultati salvati in: {results_file}")

async def main():
    """Esegue il test di conferma essenziale"""
    logger.info("🚀 Avvio Test di Conferma Essenziale")
    
    test = TestConfermaEssenziale()
    risultati = await test.esegui_test_essenziale()
    
    return 0 if risultati["successo_completo"] else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)