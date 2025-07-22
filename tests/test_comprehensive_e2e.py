# tests/test_comprehensive_e2e.py
import asyncio
import pytest
import logging
import os

# Aggiungi il percorso del backend al sys.path per trovare i moduli
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from comprehensive_e2e_test import ComprehensiveE2ETestSuite

logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_run_full_autonomous_flow():
    """
    🚀 Esegue la suite di test end-to-end completa per validare il flusso autonomo.
    
    Questo test copre tutti i 14 pilastri strategici, dalla creazione del workspace
    alla generazione dei deliverable, senza intervento umano simulato (eccetto
    l'approvazione iniziale del team).
    """
    logger.info("🚀 Inizio del test E2E completo del flusso autonomo...")
    
    from backend.executor import task_executor
    await task_executor.start()

    test_suite = ComprehensiveE2ETestSuite()
    
    try:
        report = await test_suite.run_full_test_suite()
        
        # Verifica finale basata sul report generato
        compliance_rate = report.get("strategic_pillars_compliance", {}).get("compliance_rate", 0)
        fixes_score = report.get("recent_fixes_validation", {}).get("overall_fixes_score", 0)
        
        logger.info(f"📊 Test E2E completato. Compliance Pilastri: {compliance_rate:.1f}%, Validazione Fix: {fixes_score}/4")
        
        # Aggiungi asserzioni per far fallire il test se i criteri non sono soddisfatti
        assert compliance_rate >= 80, f"La compliance dei pilastri ({compliance_rate:.1f}%) è inferiore alla soglia dell'80%"
        assert fixes_score >= 3, f"Il punteggio di validazione dei fix ({fixes_score}/4) è inferiore alla soglia di 3"
        
        logger.info("✅ Test E2E del flusso autonomo superato con successo!")
        
    except Exception as e:
        logger.error(f"❌ Test E2E fallito con un'eccezione: {e}", exc_info=True)
        pytest.fail(f"Il test E2E è fallito a causa di un'eccezione: {e}")
    finally:
        await task_executor.stop()

