import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
from uuid import uuid4, UUID
from enum import Enum

from database import (
    create_task,
    update_task_status,
    get_agent,
    list_agents as db_list_agents
)
from models import TaskStatus

logger = logging.getLogger(__name__)

class FeedbackRequestType(str, Enum):
    """Types of feedback requests"""
    TASK_APPROVAL = "task_approval"
    STRATEGY_REVIEW = "strategy_review" 
    INTERVENTION_REQUIRED = "intervention_required"
    PRIORITY_DECISION = "priority_decision"
    RESOURCE_ALLOCATION = "resource_allocation"
    CRITICAL_ASSET_VERIFICATION = "critical_asset_verification"
    QUALITY_GATE_CHECKPOINT = "quality_gate_checkpoint"
    QUALITY_GATE_FAILURE = "quality_gate_failure"
    HIGH_VALUE_DELIVERABLE = "high_value_deliverable"
    FINANCIAL_VERIFICATION = "financial_verification"
    CUSTOMER_FACING_CONTENT = "customer_facing_content"
    GOAL_CRITICAL_DELIVERABLE = "goal_critical_deliverable"
    AUTO_APPROVED = "auto_approved"

class FeedbackStatus(str, Enum):
    """Status of feedback requests"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"
    EXPIRED = "expired"

class FeedbackRequest:
    """Represents a request for human feedback"""
    def __init__(
        self,
        id: str,
        workspace_id: str,
        request_type: FeedbackRequestType,
        title: str,
        description: str,
        proposed_actions: List[Dict[str, Any]],
        context: Dict[str, Any],
        priority: str = "medium",
        timeout_hours: int = 24
    ):
        self.id = id
        self.workspace_id = workspace_id
        self.request_type = request_type
        self.title = title
        self.description = description
        self.proposed_actions = proposed_actions
        self.context = context
        self.priority = priority
        self.status = FeedbackStatus.PENDING
        self.created_at = datetime.now()
        self.expires_at = self.created_at + timedelta(hours=timeout_hours)
        self.response = None
        self.responded_at = None
        self.response_callback: Optional[Callable] = None
        self.timeout_hours = timeout_hours

class HumanFeedbackManager:
    """Manages human feedback requests and responses"""
    
    def __init__(self):
        # Keep in-memory cache for quick access
        self.pending_requests_cache: Dict[str, FeedbackRequest] = {}
        self.notification_handlers: List[Callable] = []
        self.auto_approval_rules: Dict[str, Dict[str, Any]] = {}
        
        # Start cleanup task - but only if we're in an asyncio event loop
        try:
            asyncio.create_task(self._periodic_cleanup())
        except RuntimeError:
            # No event loop running yet, the task will be started later
            logger.info("No event loop running, periodic cleanup will start when the event loop is available")
        
    def add_notification_handler(self, handler: Callable):
        """Add a handler for notifying humans of pending requests"""
        self.notification_handlers.append(handler)
    
    def set_auto_approval_rule(self, criteria: Dict[str, Any], action: str):
        """Set rules for automatic approval of certain requests"""
        rule_id = str(uuid4())
        self.auto_approval_rules[rule_id] = {
            "criteria": criteria,
            "action": action,
            "created_at": datetime.now()
        }
        return rule_id
    
    async def request_feedback(
        self,
        workspace_id: str,
        request_type: FeedbackRequestType,
        title: str,
        description: str,
        proposed_actions: List[Dict[str, Any]],
        context: Dict[str, Any],
        priority: str = "medium",
        timeout_hours: int = 24,
        response_callback: Optional[Callable] = None
    ) -> str:
        """Create a new feedback request with database persistence"""
        
        # Create FeedbackRequest object
        request = FeedbackRequest(
            id="",  # Will be set by database
            workspace_id=workspace_id,
            request_type=request_type,
            title=title,
            description=description,
            proposed_actions=proposed_actions,
            context=context,
            priority=priority,
            timeout_hours=timeout_hours
        )
        
        # Check auto-approval rules first
        if await self._check_auto_approval(request):
            return request.id
        
        # Save to database
        from database import create_human_feedback_request
        db_data = await create_human_feedback_request(
            workspace_id=workspace_id,
            request_type=request_type.value,  # Convert enum to string
            title=title,
            description=description,
            proposed_actions=proposed_actions,
            context=context,
            priority=priority,
            timeout_hours=timeout_hours
        )
        
        if not db_data:
            raise ValueError("Failed to create feedback request in database")
            
        # Update request with DB ID
        request.id = db_data["id"]
        request.response_callback = response_callback
        
        # Cache for quick access
        self.pending_requests_cache[request.id] = request
        
        # Notify handlers
        await self._notify_handlers(request)
        
        logger.info(f"Created feedback request {request.id} of type {request_type}")
        return request.id
    
    async def respond_to_request(
        self,
        request_id: str,
        response: Dict[str, Any],
        status: FeedbackStatus = FeedbackStatus.APPROVED
    ) -> bool:
        """Respond to a feedback request with database persistence"""
        
        try:
            # Get from cache or database
            request = self.pending_requests_cache.get(request_id)
            if not request:
                # Try to load from database
                from database import get_human_feedback_requests
                db_requests = await get_human_feedback_requests()
                db_request = next((r for r in db_requests if r["id"] == request_id), None)
                if db_request:
                    try:
                        request = self._deserialize_request(db_request)
                    except Exception as e:
                        logger.error(f"Error deserializing request {request_id}: {e}")
                        return False
                else:
                    logger.warning(f"Request {request_id} not found")
                    return False
            
            # Validazione finale
            if not request:
                logger.error(f"Request {request_id} is None after loading attempts")
                return False
            
            # Controllo scadenza con gestione errori
            try:
                if hasattr(request, 'expires_at') and isinstance(request.expires_at, datetime):
                    # Fix timezone comparison - ensure both datetime objects are timezone-aware
                    now = datetime.now()
                    if request.expires_at.tzinfo is not None and now.tzinfo is None:
                        # Make now timezone-aware to match request.expires_at
                        from datetime import timezone
                        now = now.replace(tzinfo=timezone.utc)
                    elif request.expires_at.tzinfo is None and now.tzinfo is not None:
                        # Make request.expires_at timezone-aware
                        from datetime import timezone
                        request.expires_at = request.expires_at.replace(tzinfo=timezone.utc)
                    
                    if request.expires_at < now:
                        status = FeedbackStatus.EXPIRED
                        logger.warning(f"Request {request_id} has expired")
                else:
                    logger.warning(f"Request {request_id} has invalid expires_at")
            except Exception as e:
                logger.error(f"Error checking expiration for {request_id}: {e}")
                # Continua comunque con il processing
            
            # Update database
            from database import update_human_feedback_request
            updated = await update_human_feedback_request(request_id, status.value, response)
            
            if not updated:
                return False
            
            # Update cache
            request.response = response
            request.status = status
            request.responded_at = datetime.now()
            
            # Remove from pending cache
            if request_id in self.pending_requests_cache:
                del self.pending_requests_cache[request_id]
            
            # Execute callback if provided
            if request.response_callback:
                try:
                    await request.response_callback(request, response)
                except Exception as e:
                    logger.error(f"Error in response callback for {request_id}: {e}")
            
            logger.info(f"Request {request_id} responded with status {status}")
            return True
            
        except Exception as e:
            logger.error(f"Unexpected error in respond_to_request for {request_id}: {e}", exc_info=True)
            return False
    
    async def get_pending_requests(self, workspace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all pending requests with database sync"""
        from database import get_human_feedback_requests
        
        # Get from database
        db_requests = await get_human_feedback_requests(workspace_id, "pending")
        
        # Update cache
        for db_req in db_requests:
            if db_req["id"] not in self.pending_requests_cache:
                self.pending_requests_cache[db_req["id"]] = self._deserialize_request(db_req)
        
        # Convert to serializable format
        return [self._serialize_request(self._deserialize_request(req)) for req in db_requests]
    
    async def cleanup_workspace_requests(self, workspace_id: str):
        """Clean up all requests for a workspace"""
        from database import delete_human_feedback_requests_by_workspace
        
        # Remove from database
        await delete_human_feedback_requests_by_workspace(workspace_id)
        
        # Remove from cache
        to_remove = [rid for rid, req in self.pending_requests_cache.items() 
                     if req.workspace_id == workspace_id]
        for rid in to_remove:
            del self.pending_requests_cache[rid]
        
        logger.info(f"Cleaned up feedback requests for workspace {workspace_id}")
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of expired requests"""
        while True:
            try:
                # Wait 1 hour
                await asyncio.sleep(3600)
                
                # Cleanup expired requests
                from database import cleanup_expired_feedback_requests
                expired_count = await cleanup_expired_feedback_requests()
                
                if expired_count > 0:
                    logger.info(f"Cleaned up {expired_count} expired feedback requests")
                
                # Clean cache of expired requests
                now = datetime.now()
                expired_in_cache = [rid for rid, req in self.pending_requests_cache.items() 
                                  if req.expires_at < now]
                for rid in expired_in_cache:
                    del self.pending_requests_cache[rid]
                    
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
    
    def _deserialize_request(self, db_data: Dict) -> FeedbackRequest:
        """Convert database data to FeedbackRequest object"""
        try:
            request = FeedbackRequest(
                id=db_data["id"],
                workspace_id=db_data["workspace_id"],
                request_type=FeedbackRequestType(db_data["request_type"]),
                title=db_data["title"],
                description=db_data["description"],
                proposed_actions=db_data["proposed_actions"],
                context=db_data["context"] or {},
                priority=db_data["priority"],
                timeout_hours=db_data["timeout_hours"]
            )
            
            # Set timestamps con controlli di sicurezza
            if db_data.get("created_at"):
                try:
                    request.created_at = datetime.fromisoformat(db_data["created_at"].replace('Z', '+00:00'))
                except (ValueError, AttributeError) as e:
                    logger.error(f"Error parsing created_at for request {db_data.get('id')}: {e}")
                    request.created_at = datetime.now()
            
            if db_data.get("expires_at"):
                try:
                    request.expires_at = datetime.fromisoformat(db_data["expires_at"].replace('Z', '+00:00'))
                except (ValueError, AttributeError) as e:
                    logger.error(f"Error parsing expires_at for request {db_data.get('id')}: {e}")
                    # Fallback: crea una data di scadenza basata su created_at + timeout
                    request.expires_at = request.created_at + timedelta(hours=request.timeout_hours)
            
            request.status = FeedbackStatus(db_data["status"])
            request.response = db_data.get("response")
            if db_data.get("responded_at"):
                try:
                    request.responded_at = datetime.fromisoformat(db_data["responded_at"].replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    request.responded_at = None
            
            return request
        except Exception as e:
            logger.error(f"Error deserializing request: {e}")
            raise
    
    def _serialize_request(self, request: FeedbackRequest) -> Dict[str, Any]:
        """Convert FeedbackRequest to dictionary"""
        return {
            "id": request.id,
            "workspace_id": request.workspace_id,
            "request_type": request.request_type.value,
            "title": request.title,
            "description": request.description,
            "proposed_actions": request.proposed_actions,
            "context": request.context,
            "priority": request.priority,
            "status": request.status.value,
            "created_at": request.created_at.isoformat(),
            "expires_at": request.expires_at.isoformat(),
            "response": request.response,
            "responded_at": request.responded_at.isoformat() if request.responded_at else None
        }
    
    async def _check_auto_approval(self, request: FeedbackRequest) -> bool:
        """Check if request matches any auto-approval rules"""
        for rule_id, rule in self.auto_approval_rules.items():
            criteria = rule["criteria"]
            
            # Simple criteria matching - can be expanded
            if (criteria.get("request_type") == request.request_type.value and
                criteria.get("priority") == request.priority):
                
                action = rule["action"]
                if action == "approve":
                    await self._auto_approve_request(request)
                    return True
                elif action == "reject":
                    await self._auto_reject_request(request)
                    return True
                    
        return False
    
    async def _notify_handlers(self, request: FeedbackRequest):
        """Notify all handlers about the new request"""
        for handler in self.notification_handlers:
            try:
                await handler(request)
            except Exception as e:
                logger.error(f"Error in notification handler: {e}")
    
    async def _auto_approve_request(self, request: FeedbackRequest):
        """Automatically approve a request"""
        response = {
            "approved": True,
            "modifications": [],
            "comment": "Auto-approved based on rules",
            "auto_approved": True
        }
        
        request.response = response
        request.status = FeedbackStatus.APPROVED
        request.responded_at = datetime.now()
        
        if request.response_callback:
            await request.response_callback(request, response)
    
    async def _auto_reject_request(self, request: FeedbackRequest):
        """Automatically reject a request"""
        response = {
            "approved": False,
            "reason": "Auto-rejected based on rules",
            "auto_rejected": True
        }
        
        request.response = response
        request.status = FeedbackStatus.REJECTED
        request.responded_at = datetime.now()
    
    def get_request_by_id(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific request by ID"""
        # Check cache first
        request = self.pending_requests_cache.get(request_id)
        if request:
            return self._serialize_request(request)
        
        # If not in cache, would need to query database
        # This would require making this method async
        return None
    
    def start_periodic_cleanup(self):
        """Start the periodic cleanup task if not already running"""
        try:
            asyncio.create_task(self._periodic_cleanup())
        except RuntimeError:
            logger.warning("Cannot start periodic cleanup: no event loop running")

# Global instance
human_feedback_manager = HumanFeedbackManager()

# Start periodic cleanup when the event loop is available
async def initialize_human_feedback_manager():
    """Initialize the human feedback manager after the event loop starts"""
    human_feedback_manager.start_periodic_cleanup()