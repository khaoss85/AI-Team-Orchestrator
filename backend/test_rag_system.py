#!/usr/bin/env python3
"""
Test completo del sistema RAG: Upload → Content Extraction → Conversational Agent Query
"""

import asyncio
import base64
import os
from datetime import datetime

# Add backend to path
import sys
sys.path.append('/Users/pelleri/Documents/ai-team-orchestrator/backend')

from services.document_manager import document_manager
from ai_agents.conversational_simple import SimpleConversationalAgent

async def test_rag_system():
    """Test completo del flusso RAG"""
    
    workspace_id = "0de74da8-d2a6-47c3-9f08-3824bf1604e0"
    
    print("=" * 80)
    print("🧪 TEST SISTEMA RAG COMPLETO")
    print("=" * 80)
    
    # 1. List existing documents
    print("\n📂 STEP 1: Lista documenti esistenti")
    print("-" * 40)
    try:
        docs = await document_manager.list_documents(workspace_id)
        print(f"✅ Trovati {len(docs)} documenti:")
        for doc in docs:
            extraction_info = ""
            if doc.extracted_text:
                extraction_info = f" [📄 {len(doc.extracted_text)} chars extracted]"
            print(f"  - {doc.filename} ({doc.mime_type}){extraction_info}")
    except Exception as e:
        print(f"❌ Errore listing documenti: {e}")
    
    # 2. Create a test PDF with real content about "15 pillars"
    print("\n📤 STEP 2: Creazione e upload PDF di test")
    print("-" * 40)
    
    # Create a simple PDF content (minimal PDF structure)
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Resources 4 0 R /MediaBox [0 0 612 792] /Contents 5 0 R >>
endobj
4 0 obj
<< /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Times-Roman >> >> >>
endobj
5 0 obj
<< /Length 500 >>
stream
BT
/F1 12 Tf
50 750 Td
(I 15 Pilastri del Sistema AI-Team-Orchestrator) Tj
0 -20 Td
(1. Goal Decomposition - Scomposizione intelligente degli obiettivi) Tj
0 -20 Td
(2. Agent Orchestration - Assegnazione semantica degli agenti) Tj
0 -20 Td
(3. Real Tool Usage - Uso di strumenti reali per contenuti autentici) Tj
0 -20 Td
(4. User Visibility - Trasparenza del processo di thinking) Tj
0 -20 Td
(5. Content Quality - Prevenzione contenuti fake) Tj
0 -20 Td
(6. Professional Display - Architettura dual-format) Tj
0 -20 Td
(7. Domain Agnostic - Funziona per qualsiasi settore) Tj
0 -20 Td
(8. Semantic Understanding - Comprende l'intent oltre le parole) Tj
0 -20 Td
(9. Auto-Adaptive - Si adatta al contesto automaticamente) Tj
0 -20 Td
(10. Robust Fallbacks - Degradazione elegante) Tj
0 -20 Td
(11. Self-Improving - Migliora con nuovi modelli AI) Tj
0 -20 Td
(12. Professional UX - Deliverable formattati professionalmente) Tj
0 -20 Td
(13. Autonomous Recovery - Recupero automatico dai fallimenti) Tj
0 -20 Td
(14. Progressive Loading - Caricamento progressivo per performance) Tj
0 -20 Td
(15. Goal-Driven System - Sistema guidato dagli obiettivi) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000220 00000 n
0000000320 00000 n
trailer
<< /Size 6 /Root 1 0 R >>
startxref
900
%%EOF"""
    
    try:
        # Upload the PDF
        doc_metadata = await document_manager.upload_document(
            workspace_id=workspace_id,
            file_content=pdf_content,
            filename=f"15_pillars_test_{datetime.now().strftime('%H%M%S')}.pdf",
            uploaded_by="test_script",
            sharing_scope="team",
            description="Documento di test con i 15 pilastri del sistema",
            tags=["test", "pillars", "documentation"]
        )
        
        print(f"✅ PDF caricato: {doc_metadata.filename}")
        print(f"  - ID: {doc_metadata.id}")
        print(f"  - Vector Store: {doc_metadata.vector_store_id}")
        
        if doc_metadata.extracted_text:
            print(f"  - 📄 Contenuto estratto: {len(doc_metadata.extracted_text)} caratteri")
            print(f"  - 🎯 Confidence: {doc_metadata.extraction_confidence:.0%}")
            print(f"  - 📊 Metodo: {doc_metadata.extraction_method}")
            print(f"  - 📑 Pagine: {doc_metadata.page_count}")
            print("\n  Preview contenuto estratto:")
            print("  " + doc_metadata.extracted_text[:200] + "...")
        else:
            print("  - ⚠️ Nessun contenuto estratto")
            
    except Exception as e:
        print(f"❌ Errore upload PDF: {e}")
        doc_metadata = None
    
    # 3. Test conversational agent with RAG
    print("\n🤖 STEP 3: Test Conversational Agent con RAG")
    print("-" * 40)
    
    agent = SimpleConversationalAgent(workspace_id, "test-rag")
    
    # Test query about pillars
    query = "Quali sono i 15 pilastri del sistema? Cercali nei documenti caricati."
    print(f"Query: {query}")
    print()
    
    try:
        response = await agent.process_message(query)
        print("Risposta Agent:")
        print("-" * 40)
        print(response.message[:1000])
        if len(response.message) > 1000:
            print("... [truncated]")
        
        if response.actions_performed:
            print("\n🔧 Azioni eseguite:")
            for action in response.actions_performed:
                print(f"  - {action}")
                
    except Exception as e:
        print(f"❌ Errore query agent: {e}")
    
    # 4. Test specific file search
    print("\n🔍 STEP 4: Test ricerca specifica nel file")
    print("-" * 40)
    
    query2 = "Cerca informazioni su 'Goal Decomposition' nei documenti"
    print(f"Query: {query2}")
    print()
    
    try:
        response2 = await agent.process_message(query2)
        print("Risposta Agent:")
        print("-" * 40)
        print(response2.message[:500])
        if len(response2.message) > 500:
            print("... [truncated]")
    except Exception as e:
        print(f"❌ Errore seconda query: {e}")
    
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETATO")
    print("=" * 80)
    
    return {
        "documents_found": len(docs) if 'docs' in locals() else 0,
        "upload_success": doc_metadata is not None,
        "extraction_success": doc_metadata.extracted_text is not None if doc_metadata else False,
        "rag_query_success": 'response' in locals()
    }

if __name__ == "__main__":
    results = asyncio.run(test_rag_system())
    
    print("\n📊 RISULTATI:")
    for key, value in results.items():
        status = "✅" if value else "❌"
        print(f"  {status} {key}: {value}")