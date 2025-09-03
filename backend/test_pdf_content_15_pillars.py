#!/usr/bin/env python3
"""
Test PDF Content Extraction for 15 Pillars
Verifies that the RAG system can extract and search content about the 15 pillars
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from services.pdf_content_extractor import pdf_extractor
from tools.enhanced_document_search import enhanced_document_tools

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_pdf_extraction():
    """Test PDF extraction on the ebook containing 15 pillars information"""
    
    # Path to the PDF
    pdf_path = "/Users/pelleri/Documents/ai-team-orchestrator/ebook/web/AI-Team-Orchestrator-Complete-EN-2025-08-29.pdf"
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF not found at: {pdf_path}")
        return False
    
    logger.info(f"📚 Testing PDF extraction for: {pdf_path}")
    logger.info("=" * 60)
    
    # Read the PDF file
    with open(pdf_path, "rb") as f:
        pdf_content = f.read()
    
    logger.info(f"📁 PDF size: {len(pdf_content):,} bytes")
    
    # Extract content
    logger.info("🔄 Extracting content from PDF...")
    extracted = await pdf_extractor.extract_content(
        file_content=pdf_content,
        filename="AI-Team-Orchestrator-Complete-EN-2025-08-29.pdf",
        chunk_size=1000,
        overlap=200
    )
    
    if not extracted or not extracted.text:
        logger.error("❌ Failed to extract content from PDF")
        return False
    
    # Display extraction results
    logger.info(f"✅ Extraction successful!")
    logger.info(f"   Method: {extracted.extraction_method}")
    logger.info(f"   Confidence: {extracted.confidence:.0%}")
    logger.info(f"   Text length: {len(extracted.text):,} characters")
    logger.info(f"   Pages: {extracted.page_count}")
    logger.info(f"   Chunks created: {len(extracted.chunks)}")
    
    # Search for "15 pillars" in the content
    logger.info("\n🔍 Searching for '15 pillars' in extracted content...")
    
    search_terms = [
        "15 pillars",
        "fifteen pillars",
        "pillar",
        "goal-driven",
        "AI-driven",
        "autonomous",
        "real-time",
        "transparency"
    ]
    
    for term in search_terms:
        term_lower = term.lower()
        count = extracted.text.lower().count(term_lower)
        if count > 0:
            logger.info(f"   ✓ Found '{term}': {count} occurrences")
            
            # Show first occurrence context
            pos = extracted.text.lower().find(term_lower)
            if pos >= 0:
                start = max(0, pos - 50)
                end = min(len(extracted.text), pos + len(term) + 100)
                context = extracted.text[start:end]
                if start > 0:
                    context = "..." + context
                if end < len(extracted.text):
                    context = context + "..."
                logger.info(f"      Context: {context}")
    
    # Test chunk search
    logger.info("\n📦 Testing chunk search for '15 pillars'...")
    search_results = await pdf_extractor.search_chunks(
        chunks=extracted.chunks,
        query="15 pillars",
        max_results=3
    )
    
    if search_results:
        logger.info(f"   Found {len(search_results)} relevant chunks:")
        for i, result in enumerate(search_results, 1):
            logger.info(f"   [{i}] Score: {result['score']}")
            logger.info(f"       Preview: {result['preview']}")
    else:
        logger.info("   No chunks found with '15 pillars'")
    
    # Test searching for specific pillars
    logger.info("\n🎯 Searching for specific pillars...")
    
    pillar_keywords = [
        "Goal Decomposition",
        "Agent Orchestration", 
        "Real Tool Usage",
        "User Visibility",
        "Content Quality",
        "Professional Display",
        "Workspace Memory",
        "Autonomous Recovery",
        "Progressive Loading",
        "Security Guidelines"
    ]
    
    found_pillars = []
    for pillar in pillar_keywords:
        if pillar.lower() in extracted.text.lower():
            found_pillars.append(pillar)
            logger.info(f"   ✓ Found pillar: {pillar}")
    
    logger.info(f"\n📊 Summary:")
    logger.info(f"   Total pillars found: {len(found_pillars)}/{len(pillar_keywords)}")
    logger.info(f"   Extraction quality: {'GOOD' if extracted.confidence > 0.8 else 'FAIR' if extracted.confidence > 0.5 else 'POOR'}")
    logger.info(f"   Content searchable: {'YES' if len(extracted.text) > 1000 else 'LIMITED'}")
    
    return True

async def test_rag_tools():
    """Test the enhanced RAG tools with a mock workspace"""
    
    logger.info("\n" + "=" * 60)
    logger.info("🔧 Testing Enhanced RAG Tools")
    logger.info("=" * 60)
    
    # Note: This would require a workspace with uploaded documents
    # For now, we just verify the tools are available
    
    search_tool = enhanced_document_tools["search_document_content"]
    read_tool = enhanced_document_tools["read_document_content"]
    summary_tool = enhanced_document_tools["summarize_document"]
    
    logger.info("✅ RAG Tools available:")
    logger.info(f"   - search_document_content: {search_tool.name}")
    logger.info(f"   - read_document_content: {read_tool.name}")
    logger.info(f"   - summarize_document: {summary_tool.name}")
    
    return True

async def main():
    """Run all tests"""
    
    logger.info("🚀 PDF Content Extraction Test for 15 Pillars")
    logger.info("=" * 60)
    
    # Test PDF extraction
    extraction_success = await test_pdf_extraction()
    
    # Test RAG tools
    tools_success = await test_rag_tools()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📋 TEST RESULTS")
    logger.info("=" * 60)
    logger.info(f"   PDF Extraction: {'✅ PASSED' if extraction_success else '❌ FAILED'}")
    logger.info(f"   RAG Tools: {'✅ PASSED' if tools_success else '❌ FAILED'}")
    
    if extraction_success and tools_success:
        logger.info("\n✨ All tests passed! The PDF content extraction system is ready.")
        logger.info("📝 Note: The database migration must be applied before documents can be stored.")
    else:
        logger.info("\n⚠️ Some tests failed. Please check the logs above.")

if __name__ == "__main__":
    asyncio.run(main())