"""
Workspace Cleanup Service
Handles complete cleanup of workspace resources including OpenAI resources
"""

import logging
import os
from typing import List
from uuid import UUID
from database import get_supabase_client
from services.document_manager import DocumentManager
from openai import OpenAI

logger = logging.getLogger(__name__)

class WorkspaceCleanupService:
    """Service for complete workspace resource cleanup"""
    
    def __init__(self):
        self.document_manager = DocumentManager()
        self.openai_client = None
        if os.getenv('OPENAI_API_KEY'):
            self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    async def cleanup_workspace_resources(self, workspace_id: str) -> dict:
        """
        Complete cleanup of all workspace resources including OpenAI resources
        
        Args:
            workspace_id: The workspace ID to cleanup
            
        Returns:
            dict: Cleanup results summary
        """
        results = {
            "workspace_id": workspace_id,
            "documents_deleted": 0,
            "vector_stores_deleted": 0,
            "openai_files_deleted": 0,
            "errors": []
        }
        
        try:
            logger.info(f"🧹 Starting complete cleanup for workspace {workspace_id}")
            
            # Step 1: Cleanup all documents (includes OpenAI files cleanup)
            await self._cleanup_workspace_documents(workspace_id, results)
            
            # Step 2: Cleanup remaining vector stores
            await self._cleanup_workspace_vector_stores(workspace_id, results)
            
            # Step 3: Verify cleanup completion
            await self._verify_cleanup_completion(workspace_id, results)
            
            logger.info(f"✅ Workspace cleanup completed: {results}")
            return results
            
        except Exception as e:
            error_msg = f"Critical error during workspace cleanup: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            # Don't raise exception to allow workspace deletion to proceed
            return results
    
    async def _cleanup_workspace_documents(self, workspace_id: str, results: dict):
        """Cleanup all documents for a workspace"""
        try:
            supabase = get_supabase_client()
            
            # Get all documents for this workspace
            documents_response = supabase.table("workspace_documents")\
                .select("id, filename, openai_file_id")\
                .eq("workspace_id", workspace_id)\
                .execute()
            
            documents = documents_response.data if documents_response.data else []
            
            logger.info(f"🗂️ Found {len(documents)} documents to cleanup for workspace {workspace_id}")
            
            # Delete each document (this will handle OpenAI resources)
            for doc in documents:
                try:
                    await self.document_manager.delete_document(doc["id"], workspace_id)
                    results["documents_deleted"] += 1
                    
                    # Track OpenAI file deletion
                    if doc.get("openai_file_id"):
                        results["openai_files_deleted"] += 1
                        
                    logger.info(f"✅ Deleted document: {doc['filename']}")
                    
                except Exception as e:
                    error_msg = f"Failed to delete document {doc['filename']}: {str(e)}"
                    logger.warning(error_msg)
                    results["errors"].append(error_msg)
                    
        except Exception as e:
            error_msg = f"Failed to cleanup workspace documents: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
    
    async def _cleanup_workspace_vector_stores(self, workspace_id: str, results: dict):
        """Cleanup remaining vector stores for a workspace"""
        try:
            supabase = get_supabase_client()
            
            # Get remaining vector stores for this workspace
            stores_response = supabase.table("workspace_vector_stores")\
                .select("id, openai_vector_store_id")\
                .eq("workspace_id", workspace_id)\
                .execute()
            
            stores = stores_response.data if stores_response.data else []
            
            logger.info(f"📦 Found {len(stores)} vector stores to cleanup for workspace {workspace_id}")
            
            # Delete each vector store from OpenAI
            for store in stores:
                try:
                    if self.openai_client and store.get("openai_vector_store_id"):
                        try:
                            # Delete from OpenAI (correct API path)
                            self.openai_client.beta.vector_stores.delete(store["openai_vector_store_id"])
                            results["vector_stores_deleted"] += 1
                            logger.info(f"✅ Deleted OpenAI vector store: {store['openai_vector_store_id']}")
                        except AttributeError:
                            # Fallback for older OpenAI client versions
                            try:
                                response = self.openai_client.delete(f"/vector_stores/{store['openai_vector_store_id']}")
                                results["vector_stores_deleted"] += 1
                                logger.info(f"✅ Deleted OpenAI vector store (fallback): {store['openai_vector_store_id']}")
                            except Exception as fallback_error:
                                error_msg = f"Failed to delete OpenAI vector store {store['openai_vector_store_id']} (both methods): {fallback_error}"
                                logger.warning(error_msg)
                                results["errors"].append(error_msg)
                    
                except Exception as e:
                    error_msg = f"Failed to delete OpenAI vector store {store['openai_vector_store_id']}: {str(e)}"
                    logger.warning(error_msg)
                    results["errors"].append(error_msg)
                    
        except Exception as e:
            error_msg = f"Failed to cleanup workspace vector stores: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
    
    async def _verify_cleanup_completion(self, workspace_id: str, results: dict):
        """Verify that cleanup was completed successfully"""
        try:
            supabase = get_supabase_client()
            
            # Check for remaining documents
            remaining_docs = supabase.table("workspace_documents")\
                .select("id", count="exact")\
                .eq("workspace_id", workspace_id)\
                .execute()
            
            # Check for remaining vector stores
            remaining_stores = supabase.table("workspace_vector_stores")\
                .select("id", count="exact")\
                .eq("workspace_id", workspace_id)\
                .execute()
            
            docs_count = remaining_docs.count if remaining_docs.count else 0
            stores_count = remaining_stores.count if remaining_stores.count else 0
            
            if docs_count > 0 or stores_count > 0:
                warning_msg = f"⚠️ Cleanup verification: {docs_count} documents, {stores_count} vector stores still remain"
                logger.warning(warning_msg)
                results["errors"].append(warning_msg)
            else:
                logger.info("✅ Cleanup verification passed: No remaining resources")
                
        except Exception as e:
            error_msg = f"Failed to verify cleanup completion: {str(e)}"
            logger.warning(error_msg)
            results["errors"].append(error_msg)
    
    async def detect_orphaned_resources(self) -> dict:
        """
        Detect OpenAI resources not linked to active workspaces
        Useful for monitoring and maintenance
        """
        try:
            supabase = get_supabase_client()
            
            # Find vector stores without matching workspaces
            orphaned_query = """
                SELECT vs.openai_vector_store_id, vs.workspace_id 
                FROM workspace_vector_stores vs
                LEFT JOIN workspaces w ON vs.workspace_id = w.id
                WHERE w.id IS NULL
            """
            
            orphaned_result = supabase.rpc("execute_sql", {"query": orphaned_query}).execute()
            
            orphaned_count = len(orphaned_result.data) if orphaned_result.data else 0
            
            if orphaned_count > 0:
                logger.warning(f"🚨 LEAK DETECTED: {orphaned_count} orphaned vector stores found")
                return {
                    "orphaned_vector_stores": orphaned_count,
                    "details": orphaned_result.data,
                    "requires_cleanup": True
                }
            else:
                logger.info("✅ No orphaned resources detected")
                return {
                    "orphaned_vector_stores": 0,
                    "requires_cleanup": False
                }
                
        except Exception as e:
            logger.error(f"Failed to detect orphaned resources: {str(e)}")
            return {
                "error": str(e),
                "detection_failed": True
            }

# Singleton instance
workspace_cleanup_service = WorkspaceCleanupService()