#!/usr/bin/env python3
"""
Enhanced Document Search with Full Content Retrieval
Provides true RAG capabilities by accessing actual document content
"""

import logging
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from database import get_supabase_client
from services.pdf_content_extractor import pdf_extractor

logger = logging.getLogger(__name__)

@dataclass
class EnhancedDocumentSearchTool:
    """
    Advanced document search that retrieves actual content, not just metadata
    Implements true RAG (Retrieval-Augmented Generation) capabilities
    """
    name: str = "search_document_content"
    description: str = "Search and retrieve actual content from uploaded documents"
    
    async def execute(
        self,
        query: str,
        workspace_id: str,
        max_results: int = 3,
        include_full_text: bool = False,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Search documents and retrieve actual content for RAG
        
        Args:
            query: Search query
            workspace_id: Workspace to search in
            max_results: Maximum number of results
            include_full_text: Whether to include full extracted text
            context: Additional context
            
        Returns:
            Formatted search results with actual content
        """
        
        try:
            supabase = get_supabase_client()
            
            # Step 1: Search for documents with extracted content
            logger.info(f"🔍 Searching for documents with query: {query}")
            
            # Get all documents in workspace that have extracted text
            documents = supabase.table("workspace_documents")\
                .select("*")\
                .eq("workspace_id", workspace_id)\
                .not_.is_("extracted_text", None)\
                .execute()
            
            if not documents.data:
                # Fallback to documents without extracted text
                all_docs = supabase.table("workspace_documents")\
                    .select("*")\
                    .eq("workspace_id", workspace_id)\
                    .execute()
                
                if not all_docs.data:
                    return "📁 No documents found in this workspace."
                else:
                    return f"""📁 Found {len(all_docs.data)} documents but none have extracted content.
                    
Documents need to be re-uploaded or processed for content extraction.
Available documents (metadata only):
{self._format_document_list(all_docs.data)}"""
            
            # Step 2: Search through extracted content
            search_results = []
            query_lower = query.lower()
            
            for doc in documents.data:
                relevance_score = 0
                matching_chunks = []
                
                # Search in extracted text
                extracted_text = doc.get("extracted_text", "")
                if extracted_text:
                    extracted_lower = extracted_text.lower()
                    
                    # Calculate relevance score
                    if query_lower in extracted_lower:
                        relevance_score += 10
                        
                        # Find matching context
                        position = extracted_lower.find(query_lower)
                        if position >= 0:
                            # Extract context around match (200 chars before and after)
                            start = max(0, position - 200)
                            end = min(len(extracted_text), position + len(query) + 200)
                            context_snippet = extracted_text[start:end]
                            
                            # Clean up snippet
                            if start > 0:
                                context_snippet = "..." + context_snippet
                            if end < len(extracted_text):
                                context_snippet = context_snippet + "..."
                            
                            matching_chunks.append({
                                "position": position,
                                "context": context_snippet,
                                "exact_match": True
                            })
                    
                    # Check for word-level matches
                    query_words = query_lower.split()
                    for word in query_words:
                        if len(word) > 2 and word in extracted_lower:
                            relevance_score += 1
                
                # Search in text chunks if available
                if doc.get("text_chunks"):
                    try:
                        chunks = json.loads(doc["text_chunks"]) if isinstance(doc["text_chunks"], str) else doc["text_chunks"]
                        
                        for chunk in chunks:
                            chunk_text = chunk.get("text", "").lower()
                            if query_lower in chunk_text:
                                relevance_score += 5
                                matching_chunks.append({
                                    "chunk_id": chunk.get("id"),
                                    "context": chunk.get("text", "")[:300],
                                    "exact_match": True
                                })
                    except Exception as e:
                        logger.warning(f"Failed to parse chunks: {e}")
                
                # Add to results if relevant
                if relevance_score > 0:
                    search_results.append({
                        "document": doc,
                        "score": relevance_score,
                        "matching_chunks": matching_chunks[:3]  # Top 3 matches
                    })
            
            # Step 3: Sort by relevance and format results
            search_results.sort(key=lambda x: x["score"], reverse=True)
            top_results = search_results[:max_results]
            
            if not top_results:
                return f"""📭 No matching content found for query: "{query}"
                
Searched through {len(documents.data)} documents with extracted content.
Try different search terms or ensure documents contain the information you're looking for."""
            
            # Step 4: Format results with actual content
            formatted_results = [f"🔍 **Search Results for**: \"{query}\"\n"]
            formatted_results.append(f"📊 Found matches in {len(search_results)} documents\n")
            
            for i, result in enumerate(top_results, 1):
                doc = result["document"]
                formatted_results.append(f"\n{'='*60}")
                formatted_results.append(f"📄 **{i}. {doc['filename']}**")
                formatted_results.append(f"   📈 Relevance Score: {result['score']}")
                formatted_results.append(f"   📅 Uploaded: {doc.get('upload_date', 'Unknown')}")
                
                if doc.get("extraction_confidence"):
                    formatted_results.append(f"   🎯 Extraction Confidence: {doc['extraction_confidence']:.0%}")
                
                # Add matching content
                if result["matching_chunks"]:
                    formatted_results.append(f"\n   **Matching Content:**")
                    for j, chunk in enumerate(result["matching_chunks"], 1):
                        formatted_results.append(f"\n   [{j}] {chunk['context']}")
                
                # Optionally include full text
                if include_full_text and doc.get("extracted_text"):
                    full_text = doc["extracted_text"]
                    if len(full_text) > 1000:
                        full_text = full_text[:1000] + "...[truncated]"
                    formatted_results.append(f"\n   **Full Extracted Text:**")
                    formatted_results.append(f"   {full_text}")
            
            return "\n".join(formatted_results)
            
        except Exception as e:
            logger.error(f"Enhanced document search failed: {e}")
            return f"❌ Document search error: {str(e)}"
    
    def _format_document_list(self, documents: List[Dict]) -> str:
        """Format document list for display"""
        
        lines = []
        for doc in documents[:5]:  # Show first 5
            lines.append(f"  • {doc['filename']} ({doc.get('file_size', 0)} bytes)")
        
        if len(documents) > 5:
            lines.append(f"  ... and {len(documents) - 5} more")
        
        return "\n".join(lines)

@dataclass 
class DocumentContentRetrievalTool:
    """
    Tool to retrieve and display full document content
    Enables AI to read and understand complete documents
    """
    name: str = "read_document_content"
    description: str = "Read the full content of a specific document"
    
    async def execute(
        self,
        document_id: Optional[str] = None,
        filename: Optional[str] = None,
        workspace_id: str = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Retrieve full content of a specific document
        
        Args:
            document_id: Document ID to retrieve
            filename: Alternative - search by filename
            workspace_id: Workspace ID
            context: Additional context
            
        Returns:
            Full document content or error message
        """
        
        try:
            if not workspace_id:
                workspace_id = context.get("workspace_id") if context else None
            
            if not workspace_id:
                return "❌ Error: workspace_id required"
            
            supabase = get_supabase_client()
            
            # Find document
            if document_id:
                result = supabase.table("workspace_documents")\
                    .select("*")\
                    .eq("id", document_id)\
                    .eq("workspace_id", workspace_id)\
                    .execute()
            elif filename:
                result = supabase.table("workspace_documents")\
                    .select("*")\
                    .eq("filename", filename)\
                    .eq("workspace_id", workspace_id)\
                    .execute()
            else:
                return "❌ Error: Either document_id or filename required"
            
            if not result.data:
                return f"❌ Document not found"
            
            doc = result.data[0]
            
            # Check if content is extracted
            if not doc.get("extracted_text"):
                return f"""📄 **{doc['filename']}**
                
⚠️ This document has not been processed for content extraction.

**Document Information:**
- Type: {doc.get('mime_type', 'Unknown')}
- Size: {doc.get('file_size', 0)} bytes
- Uploaded: {doc.get('upload_date', 'Unknown')}
- Description: {doc.get('description', 'No description')}

To read this document's content, it needs to be re-uploaded with content extraction enabled."""
            
            # Return extracted content
            extracted_text = doc["extracted_text"]
            confidence = doc.get("extraction_confidence", 0)
            
            response = [f"📄 **{doc['filename']}**"]
            response.append(f"🎯 Extraction Confidence: {confidence:.0%}")
            response.append(f"📏 Content Length: {len(extracted_text)} characters")
            response.append(f"\n{'='*60}")
            response.append("\n**Document Content:**\n")
            response.append(extracted_text)
            
            return "\n".join(response)
            
        except Exception as e:
            logger.error(f"Document content retrieval failed: {e}")
            return f"❌ Error retrieving document content: {str(e)}"

@dataclass
class DocumentSummaryTool:
    """
    Tool to generate AI-powered summaries of document content
    """
    name: str = "summarize_document"
    description: str = "Generate an AI summary of document content"
    
    async def execute(
        self,
        document_id: Optional[str] = None,
        filename: Optional[str] = None,
        workspace_id: str = None,
        summary_type: str = "brief",  # brief, detailed, key_points
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate AI summary of document content
        
        Args:
            document_id: Document ID
            filename: Alternative - search by filename
            workspace_id: Workspace ID
            summary_type: Type of summary (brief/detailed/key_points)
            context: Additional context
            
        Returns:
            AI-generated summary
        """
        
        try:
            if not workspace_id:
                workspace_id = context.get("workspace_id") if context else None
            
            if not workspace_id:
                return "❌ Error: workspace_id required"
            
            # First, get the document content
            content_tool = DocumentContentRetrievalTool()
            content_result = await content_tool.execute(
                document_id=document_id,
                filename=filename,
                workspace_id=workspace_id,
                context=context
            )
            
            if "❌" in content_result or "⚠️" in content_result:
                return content_result
            
            # Extract the actual content from the result
            lines = content_result.split("\n")
            content_start = False
            content_lines = []
            
            for line in lines:
                if "**Document Content:**" in line:
                    content_start = True
                    continue
                if content_start:
                    content_lines.append(line)
            
            document_text = "\n".join(content_lines)
            
            if not document_text.strip():
                return "❌ No content available for summarization"
            
            # Generate summary using OpenAI
            try:
                from openai import OpenAI
                client = OpenAI()
                
                # Prepare prompt based on summary type
                if summary_type == "brief":
                    prompt = "Provide a brief 2-3 sentence summary of the following document:"
                elif summary_type == "detailed":
                    prompt = "Provide a detailed summary with main sections and key information from the following document:"
                elif summary_type == "key_points":
                    prompt = "Extract and list the key points and important information from the following document:"
                else:
                    prompt = "Summarize the following document:"
                
                # Truncate if too long for API
                max_chars = 10000
                if len(document_text) > max_chars:
                    document_text = document_text[:max_chars] + "...[truncated for summary]"
                
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that summarizes documents clearly and accurately."},
                        {"role": "user", "content": f"{prompt}\n\n{document_text}"}
                    ],
                    temperature=0.3,
                    max_tokens=500
                )
                
                summary = response.choices[0].message.content
                
                # Get document info from original content
                doc_info = lines[0] if lines else "Document"
                
                return f"""{doc_info}

📝 **AI Summary ({summary_type})**
{'='*60}

{summary}

{'='*60}
📊 Summary generated from {len(document_text)} characters of content."""
                
            except Exception as e:
                logger.error(f"AI summary generation failed: {e}")
                return f"❌ Failed to generate AI summary: {str(e)}"
            
        except Exception as e:
            logger.error(f"Document summary failed: {e}")
            return f"❌ Error creating document summary: {str(e)}"

# Export enhanced tools
enhanced_document_tools = {
    "search_document_content": EnhancedDocumentSearchTool(),
    "read_document_content": DocumentContentRetrievalTool(),
    "summarize_document": DocumentSummaryTool()
}