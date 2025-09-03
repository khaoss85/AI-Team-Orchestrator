#!/usr/bin/env python3
"""
Test RAG functionality with the current workspace containing book.pdf
"""

import asyncio
import sys
sys.path.append('/Users/pelleri/Documents/ai-team-orchestrator/backend')

from ai_agents.conversational_simple import SimpleConversationalAgent
from services.document_manager import document_manager

async def test_current_workspace_rag():
    """Test RAG with existing book.pdf in current workspace"""
    
    workspace_id = "f35639dc-12ae-4720-882d-3e35a70a79b8"
    
    print("=" * 80)
    print("🧪 TEST RAG SISTEMA CON WORKSPACE CORRENTE")
    print("=" * 80)
    
    # 1. Check existing documents
    print("\n📂 STEP 1: Lista documenti nel workspace corrente")
    print("-" * 50)
    try:
        docs = await document_manager.list_documents(workspace_id)
        print(f"✅ Trovati {len(docs)} documenti:")
        for doc in docs:
            extraction_info = ""
            if doc.extracted_text:
                extraction_info = f" [📄 {len(doc.extracted_text)} chars extracted]"
                print(f"  - {doc.filename} ({doc.mime_type}){extraction_info}")
                print(f"    📊 Confidence: {doc.extraction_confidence:.0%}")
                print(f"    🔧 Metodo: {doc.extraction_method}")
                print(f"    📑 Chunks: {len(doc.text_chunks) if doc.text_chunks else 0}")
                if doc.extracted_text:
                    preview = doc.extracted_text[:200] + "..." if len(doc.extracted_text) > 200 else doc.extracted_text
                    print(f"    👀 Preview: {preview}")
            else:
                print(f"  - {doc.filename} ({doc.mime_type}) [⚠️ No content extracted]")
    except Exception as e:
        print(f"❌ Errore listing documenti: {e}")
        return
    
    # 2. Test conversational agent with RAG
    print("\n🤖 STEP 2: Test Conversational Agent - Domanda sui 15 pilastri")
    print("-" * 50)
    
    agent = SimpleConversationalAgent(workspace_id, "test-rag-current")
    
    # Test the exact question that failed before
    query = "Quali sono i 15 pilastri del nostro framework AI? Cercali nel documento book.pdf caricato."
    print(f"Query: {query}")
    print()
    
    try:
        response = await agent.process_message(query)
        print("Risposta Agent:")
        print("-" * 50)
        print(response.message)
        
        if response.actions_performed:
            print(f"\n🔧 Azioni eseguite ({len(response.actions_performed)}):")
            for action in response.actions_performed:
                print(f"  - {action}")
                
    except Exception as e:
        print(f"❌ Errore query agent: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. Test specific content search
    print("\n🔍 STEP 3: Test ricerca specifica 'Goal Decomposition'")
    print("-" * 50)
    
    query2 = "Cerca informazioni su 'Goal Decomposition' nel documento book.pdf"
    print(f"Query: {query2}")
    print()
    
    try:
        response2 = await agent.process_message(query2)
        print("Risposta Agent:")
        print("-" * 50)
        print(response2.message[:800])
        if len(response2.message) > 800:
            print("... [truncated]")
    except Exception as e:
        print(f"❌ Errore seconda query: {e}")
    
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETATO")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_current_workspace_rag())