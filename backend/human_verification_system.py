#!/usr/bin/env python3

import logging
import json
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field
from uuid import uuid4

logger = logging.getLogger(__name__)

class VerificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class VerificationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class VerificationCheckpoint(BaseModel):
    """Human verification checkpoint for critical deliverables"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    workspace_id: str
    task_id: str
    task_name: str
    asset_type: str
    
    # Verification details
    verification_type: str  # "quality_gate", "content_approval", "business_validation"
    priority: VerificationPriority
    timeout_hours: int = 24
    
    # Content to verify
    deliverable_data: Dict[str, Any]
    quality_assessment: Optional[Dict[str, Any]] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    
    # Verification questions/criteria
    verification_criteria: List[str] = Field(default_factory=list)
    verification_questions: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Status tracking
    status: VerificationStatus = VerificationStatus.PENDING
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    expires_at: str = Field(default_factory=lambda: (datetime.now() + timedelta(hours=24)).isoformat())
    
    # Human response
    reviewer_feedback: Optional[str] = None
    approval_reason: Optional[str] = None
    rejection_reason: Optional[str] = None
    reviewer_notes: Optional[str] = None
    reviewed_at: Optional[str] = None
    
    # Actions to take based on verification
    on_approval_actions: List[Dict[str, Any]] = Field(default_factory=list)
    on_rejection_actions: List[Dict[str, Any]] = Field(default_factory=list)

class HumanVerificationSystem:
    """
    🚨 HUMAN VERIFICATION SYSTEM - Enhanced quality gates with human oversight
    
    This system creates checkpoints where humans must verify critical deliverables
    before they can be marked as completed and count toward goal progress.
    """
    
    def __init__(self):
        self.verification_checkpoints = {}  # In-memory storage for demo
        self.auto_approve_threshold = 0.95  # Quality score above which to auto-approve
        self.auto_reject_threshold = 0.3    # Quality score below which to auto-reject
        
        # Critical asset types that always require human verification
        self.critical_asset_types = {
            "contact_database",
            "email_sequence", 
            "financial_plan",
            "strategic_plan",
            "business_analysis"
        }
        
        # High-value deliverables by name patterns
        self.high_value_patterns = [
            "contatti icp", "contact database", "email sequences", 
            "competitor analysis", "strategic plan", "budget", 
            "financial analysis", "client proposal"
        ]
    
    def get_checkpoint_by_task_id(self, task_id: str) -> Optional[VerificationCheckpoint]:
        """🔍 Get existing checkpoint for a task to prevent duplicates"""
        for checkpoint in self.verification_checkpoints.values():
            if checkpoint.task_id == task_id and checkpoint.status == VerificationStatus.PENDING:
                return checkpoint
        return None
    
    def get_checkpoint_by_workspace_and_asset(self, workspace_id: str, asset_type: str) -> Optional[VerificationCheckpoint]:
        """🔍 Get existing checkpoint by workspace and asset type to prevent workspace-level duplicates"""
        for checkpoint in self.verification_checkpoints.values():
            if (checkpoint.workspace_id == workspace_id and 
                checkpoint.asset_type == asset_type and 
                checkpoint.status == VerificationStatus.PENDING):
                return checkpoint
        return None
    
    async def create_verification_checkpoint(
        self,
        workspace_id: str,
        task_id: str,
        task_name: str,
        asset_type: str,
        deliverable_data: Dict[str, Any],
        quality_assessment: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[VerificationCheckpoint]:
        """
        🎯 CREATE VERIFICATION CHECKPOINT - Determines if human verification is needed
        """
        try:
            # 🚫 ENHANCED DUPLICATE PREVENTION: Check multiple levels
            
            # Level 1: Check by task_id
            existing_task_checkpoint = self.get_checkpoint_by_task_id(task_id)
            if existing_task_checkpoint:
                logger.info(f"🔄 DUPLICATE PREVENTED (TASK): Task {task_id} already has checkpoint {existing_task_checkpoint.id}")
                return existing_task_checkpoint
            
            # Level 2: Check by workspace + asset type (prevents workspace-level duplicates)
            existing_workspace_checkpoint = self.get_checkpoint_by_workspace_and_asset(workspace_id, asset_type)
            if existing_workspace_checkpoint:
                logger.info(f"🔄 DUPLICATE PREVENTED (WORKSPACE): Workspace {workspace_id} already has {asset_type} checkpoint {existing_workspace_checkpoint.id}")
                return existing_workspace_checkpoint
            
            # Level 3: Check database for pending requests
            if await self._has_duplicate_request_enhanced(workspace_id, task_id, asset_type):
                logger.info(f"🔄 DUPLICATE PREVENTED (DATABASE): Similar request already exists for workspace {workspace_id}")
                return None
            
            # Determine if this deliverable needs human verification
            needs_verification, priority, verification_type = await self._assess_verification_need(
                task_name, asset_type, deliverable_data, quality_assessment
            )
            
            if not needs_verification:
                logger.info(f"✅ NO VERIFICATION NEEDED: Task {task_id} ({asset_type}) approved automatically")
                return None
            
            # Generate verification criteria and questions
            criteria, questions = await self._generate_verification_criteria(
                asset_type, task_name, deliverable_data, quality_assessment
            )
            
            # Determine timeout based on priority
            timeout_hours = self._get_verification_timeout(priority)
            
            # Create verification checkpoint
            checkpoint = VerificationCheckpoint(
                workspace_id=workspace_id,
                task_id=task_id,
                task_name=task_name,
                asset_type=asset_type,
                verification_type=verification_type,
                priority=priority,
                timeout_hours=timeout_hours,
                deliverable_data=deliverable_data,
                quality_assessment=quality_assessment,
                context=context or {},
                verification_criteria=criteria,
                verification_questions=questions,
                expires_at=(datetime.now() + timedelta(hours=timeout_hours)).isoformat(),
                on_approval_actions=self._generate_approval_actions(task_id),
                on_rejection_actions=self._generate_rejection_actions(task_id, asset_type)
            )
            
            # Store checkpoint
            self.verification_checkpoints[checkpoint.id] = checkpoint
            
            # Create human feedback request in database with final duplicate check
            await self._create_database_feedback_request(checkpoint)
            
            logger.warning(f"🚨 VERIFICATION REQUIRED: {verification_type} for task {task_id} "
                          f"({asset_type}, priority: {priority.value}, expires in {timeout_hours}h)")
            
            return checkpoint
            
        except Exception as e:
            logger.error(f"Error creating verification checkpoint: {e}", exc_info=True)
            return None
    
    async def _assess_verification_need(
        self,
        task_name: str,
        asset_type: str,
        deliverable_data: Dict[str, Any],
        quality_assessment: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, VerificationPriority, str]:
        """
        🔍 SMART VERIFICATION ASSESSMENT - Determines verification requirements
        """
        
        task_lower = task_name.lower()
        
        # 🚨 ALWAYS VERIFY: Critical asset types
        if asset_type in self.critical_asset_types:
            return True, VerificationPriority.HIGH, "critical_asset_verification"
        
        # 🎯 HIGH-VALUE DELIVERABLES: Based on task name patterns
        if any(pattern in task_lower for pattern in self.high_value_patterns):
            return True, VerificationPriority.HIGH, "high_value_deliverable"
        
        # 📊 QUALITY-BASED VERIFICATION: Based on quality assessment
        if quality_assessment:
            quality_score = quality_assessment.get("overall_score", 0.0)
            quality_issues = quality_assessment.get("quality_issues", [])
            
            # Auto-approve if quality is excellent
            if quality_score >= self.auto_approve_threshold and not quality_issues:
                return False, VerificationPriority.LOW, "auto_approved"
            
            # Auto-reject if quality is terrible (will create rejection checkpoint)
            if quality_score <= self.auto_reject_threshold:
                return True, VerificationPriority.CRITICAL, "quality_gate_failure"
            
            # Require verification for medium quality
            if quality_score < 0.8 or len(quality_issues) > 2:
                return True, VerificationPriority.MEDIUM, "quality_gate_checkpoint"
        
        # 💰 FINANCIAL/BUDGET DELIVERABLES: Always verify
        if any(keyword in task_lower for keyword in ["budget", "financial", "cost", "revenue", "investment"]):
            return True, VerificationPriority.HIGH, "financial_verification"
        
        # 📧 CUSTOMER-FACING CONTENT: Verify email sequences and marketing materials
        if any(keyword in task_lower for keyword in ["email", "customer", "client", "marketing", "campaign"]):
            return True, VerificationPriority.MEDIUM, "customer_facing_content"
        
        # 🎯 GOAL-CRITICAL DELIVERABLES: Check if deliverable directly impacts workspace goals
        if await self._is_goal_critical_deliverable(task_name, deliverable_data):
            return True, VerificationPriority.HIGH, "goal_critical_deliverable"
        
        # Default: No verification needed for low-risk deliverables
        return False, VerificationPriority.LOW, "auto_approved"
    
    async def _generate_verification_criteria(
        self,
        asset_type: str,
        task_name: str,
        deliverable_data: Dict[str, Any],
        quality_assessment: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[str], List[Dict[str, str]]]:
        """
        📋 GENERATE VERIFICATION CRITERIA - Creates specific verification questions
        """
        
        criteria = []
        questions = []
        
        # 📊 UNIVERSAL QUALITY CRITERIA
        criteria.extend([
            "Deliverable contains real, actionable data (not examples or placeholders)",
            "Content is appropriate for business use without modification",
            "Information is accurate and professionally presented",
            "Deliverable meets the original task requirements"
        ])
        
        questions.append({
            "question": "Does this deliverable contain real, usable business data (not fake examples)?",
            "type": "yes_no",
            "critical": True
        })
        
        # 🎯 ASSET-SPECIFIC CRITERIA
        if asset_type == "contact_database":
            criteria.extend([
                "All contacts have valid, real email addresses",
                "Company information is accurate and verifiable", 
                "Contacts match the specified target criteria (ICP)",
                "Contact details are complete (name, email, company, role)"
            ])
            
            questions.extend([
                {
                    "question": "Are these real, contactable business professionals (not fake names)?",
                    "type": "yes_no",
                    "critical": True
                },
                {
                    "question": "Do the contacts match our Ideal Customer Profile (ICP)?",
                    "type": "yes_no", 
                    "critical": True
                }
            ])
        
        elif asset_type == "email_sequence":
            criteria.extend([
                "Email subject lines are compelling and professional",
                "Email content is personalized and relevant",
                "Call-to-actions are clear and actionable",
                "Sequence follows logical progression and timing"
            ])
            
            questions.extend([
                {
                    "question": "Are the emails ready to send to real customers without modification?",
                    "type": "yes_no",
                    "critical": True
                },
                {
                    "question": "Is the content professional and brand-appropriate?",
                    "type": "yes_no",
                    "critical": True
                }
            ])
        
        elif asset_type == "business_analysis":
            criteria.extend([
                "Analysis is based on real data and research",
                "Insights are actionable and business-relevant",
                "Conclusions are well-supported by evidence",
                "Recommendations are specific and implementable"
            ])
            
            questions.extend([
                {
                    "question": "Is this analysis based on real market data (not generic examples)?",
                    "type": "yes_no",
                    "critical": True
                },
                {
                    "question": "Are the recommendations specific and actionable?",
                    "type": "yes_no",
                    "critical": False
                }
            ])
        
        elif asset_type == "financial_plan":
            criteria.extend([
                "Financial projections are realistic and well-justified",
                "All costs and revenues are properly categorized",
                "Assumptions are clearly stated and reasonable",
                "Plan aligns with business objectives"
            ])
            
            questions.extend([
                {
                    "question": "Are the financial projections realistic and based on real data?",
                    "type": "yes_no",
                    "critical": True
                },
                {
                    "question": "Are all major cost categories included?",
                    "type": "yes_no",
                    "critical": True
                }
            ])
        
        elif asset_type == "process_document":
            criteria.extend([
                "Process documentation is clear and complete",
                "Steps are actionable and well-defined",
                "Roles and responsibilities are clearly specified",
                "Document is ready for immediate implementation"
            ])
            
            questions.extend([
                {
                    "question": "Is this process document complete and ready for team implementation?",
                    "type": "yes_no",
                    "critical": True
                },
                {
                    "question": "Are all roles and responsibilities clearly defined?",
                    "type": "yes_no",
                    "critical": False
                }
            ])
        
        elif asset_type == "generic_deliverable":
            criteria.extend([
                "Deliverable meets the stated requirements",
                "Content is professional and complete",
                "Output is actionable and business-ready"
            ])
            
            questions.extend([
                {
                    "question": "Does this deliverable meet the original task requirements?",
                    "type": "yes_no",
                    "critical": True
                },
                {
                    "question": "Is the content professional and ready for business use?",
                    "type": "yes_no",
                    "critical": False
                }
            ])
        
        # 📊 QUALITY-SPECIFIC CRITERIA
        if quality_assessment:
            quality_score = quality_assessment.get("overall_score", 0.0)
            quality_issues = quality_assessment.get("quality_issues", [])
            
            if quality_score < 0.8:
                criteria.append(f"Quality score is {quality_score:.1%} - review for improvement opportunities")
                questions.append({
                    "question": f"Given the quality score of {quality_score:.1%}, is this acceptable for business use?",
                    "type": "yes_no",
                    "critical": False
                })
            
            if quality_issues:
                criteria.append(f"Address quality issues: {', '.join(quality_issues)}")
                questions.append({
                    "question": f"Quality issues detected: {', '.join(quality_issues)}. Are these acceptable?",
                    "type": "yes_no",
                    "critical": True
                })
        
        return criteria, questions
    
    async def _is_goal_critical_deliverable(self, task_name: str, deliverable_data: Dict[str, Any]) -> bool:
        """Check if deliverable directly impacts workspace goals"""
        
        # Look for numerical achievements that would directly impact goals
        task_lower = task_name.lower()
        
        goal_critical_patterns = [
            "50 contatti", "50 contacts", "3 sequenze", "3 sequences", 
            "30% open", "10% click", "target", "obiettivo"
        ]
        
        return any(pattern in task_lower for pattern in goal_critical_patterns)
    
    def _get_verification_timeout(self, priority: VerificationPriority) -> int:
        """Get verification timeout based on priority"""
        
        timeout_map = {
            VerificationPriority.CRITICAL: 2,   # 2 hours for critical
            VerificationPriority.HIGH: 8,      # 8 hours for high
            VerificationPriority.MEDIUM: 24,   # 24 hours for medium  
            VerificationPriority.LOW: 72       # 72 hours for low
        }
        
        return timeout_map.get(priority, 24)
    
    def _generate_approval_actions(self, task_id: str) -> List[Dict[str, Any]]:
        """Generate actions to take when verification is approved"""
        
        return [
            {
                "type": "update_task_status",
                "task_id": task_id,
                "status": "completed",
                "reason": "Human verification approved"
            },
            {
                "type": "update_goal_progress",
                "task_id": task_id,
                "reason": "Verified deliverable approved for goal progress"
            },
            {
                "type": "log_verification_result",
                "result": "approved",
                "task_id": task_id
            }
        ]
    
    def _generate_rejection_actions(self, task_id: str, asset_type: str) -> List[Dict[str, Any]]:
        """Generate actions to take when verification is rejected"""
        
        return [
            {
                "type": "update_task_status", 
                "task_id": task_id,
                "status": "needs_enhancement",
                "reason": "Human verification rejected"
            },
            {
                "type": "create_enhancement_task",
                "parent_task_id": task_id,
                "task_name": f"Enhance {asset_type} based on verification feedback",
                "priority": "high"
            },
            {
                "type": "log_verification_result",
                "result": "rejected",
                "task_id": task_id
            }
        ]
    
    async def _create_database_feedback_request(self, checkpoint: VerificationCheckpoint):
        """Create human feedback request in database"""
        
        try:
            from database import create_human_feedback_request
            
            # Final duplicate check before database creation
            if await self._has_duplicate_request_enhanced(checkpoint.workspace_id, checkpoint.task_id, checkpoint.asset_type):
                logger.info(f"🔄 FINAL DUPLICATE CHECK: Skipping verification request for task {checkpoint.task_id}")
                # Remove from in-memory storage since we're not creating the DB request
                if checkpoint.id in self.verification_checkpoints:
                    del self.verification_checkpoints[checkpoint.id]
                return
            
            # Prepare proposed actions
            proposed_actions = [
                {
                    "action": "approve",
                    "label": "Approve Deliverable",
                    "description": "Mark deliverable as completed and update goal progress",
                    "actions": checkpoint.on_approval_actions
                },
                {
                    "action": "reject",
                    "label": "Reject - Needs Enhancement", 
                    "description": "Send back for improvement with specific feedback",
                    "actions": checkpoint.on_rejection_actions
                }
            ]
            
            # Create context with verification details
            context = {
                "verification_checkpoint_id": checkpoint.id,
                "asset_type": checkpoint.asset_type,
                "verification_criteria": checkpoint.verification_criteria,
                "verification_questions": checkpoint.verification_questions,
                "quality_assessment": checkpoint.quality_assessment,
                "deliverable_preview": self._create_deliverable_preview(checkpoint.deliverable_data)
            }
            
            # Create user-friendly title and description
            user_friendly_title = self._generate_user_friendly_title(checkpoint)
            detailed_description = self._generate_detailed_description(checkpoint)
            
            # Create feedback request
            request = await create_human_feedback_request(
                workspace_id=checkpoint.workspace_id,
                request_type=checkpoint.verification_type,
                title=user_friendly_title,
                description=detailed_description,
                proposed_actions=proposed_actions,
                context=context,
                priority=checkpoint.priority.value,
                timeout_hours=checkpoint.timeout_hours
            )
            
            if request:
                logger.info(f"📨 VERIFICATION REQUEST CREATED: {request['id']} for task {checkpoint.task_id}")
            
        except Exception as e:
            logger.error(f"Error creating database feedback request: {e}")
    
    def _generate_user_friendly_title(self, checkpoint: VerificationCheckpoint) -> str:
        """Generate user-friendly title for verification request"""
        
        # Extract business-meaningful title from task name
        task_name = checkpoint.task_name
        asset_type = checkpoint.asset_type
        
        # Remove technical prefixes/suffixes
        clean_name = task_name
        if "HANDOFF from" in clean_name:
            # Extract the actual work being done
            clean_name = clean_name.split("for Task ID:")[0].replace("HANDOFF from Hubspot Campaign Specialist Agent", "Email Campaign Setup")
        
        # Asset type specific improvements
        asset_friendly_names = {
            "email_sequence": "Email Marketing Campaign",
            "contact_database": "Customer Contact List",
            "strategic_plan": "Strategic Business Plan",
            "financial_plan": "Financial Planning Document", 
            "process_document": "Business Process Guide",
            "analysis_report": "Business Analysis Report"
        }
        
        asset_display = asset_friendly_names.get(asset_type, asset_type.replace("_", " ").title())
        
        # Generate meaningful title
        if "setup" in clean_name.lower() or "implement" in clean_name.lower():
            return f"Review {asset_display} Setup"
        elif "research" in clean_name.lower() or "define" in clean_name.lower():
            return f"Approve {asset_display} Research"
        elif "plan" in clean_name.lower():
            return f"Validate {asset_display}"
        else:
            return f"Review {asset_display} Deliverable"
    
    def _generate_detailed_description(self, checkpoint: VerificationCheckpoint) -> str:
        """Generate detailed, business-focused description"""
        
        asset_type = checkpoint.asset_type
        task_name = checkpoint.task_name
        
        # Get quality score for context
        quality_score = 0.0
        quality_issues = []
        if checkpoint.quality_assessment:
            quality_score = checkpoint.quality_assessment.get("overall_score", 0.0)
            quality_issues = checkpoint.quality_assessment.get("quality_issues", [])
        
        # Asset-specific descriptions
        descriptions = {
            "email_sequence": f"""
**Business Impact**: Email marketing campaign ready for implementation
**What to Review**: Email templates, targeting strategy, and performance tracking setup
**Quality Score**: {quality_score:.1%} ({len(quality_issues)} issues identified)
**Why Review Needed**: Ensure emails are professional, compliant, and will drive engagement
            """,
            "contact_database": f"""
**Business Impact**: Customer contact database for sales and marketing outreach  
**What to Review**: Contact quality, data completeness, and GDPR compliance
**Quality Score**: {quality_score:.1%} ({len(quality_issues)} issues identified)
**Why Review Needed**: Verify contacts are real, reachable business professionals
            """,
            "strategic_plan": f"""
**Business Impact**: Strategic roadmap for business growth and operations
**What to Review**: Goals alignment, resource allocation, and timeline feasibility  
**Quality Score**: {quality_score:.1%} ({len(quality_issues)} issues identified)
**Why Review Needed**: Ensure plan is actionable and aligned with business objectives
            """,
            "financial_plan": f"""
**Business Impact**: Financial projections and budget planning
**What to Review**: Revenue forecasts, cost estimates, and investment requirements
**Quality Score**: {quality_score:.1%} ({len(quality_issues)} issues identified) 
**Why Review Needed**: Verify financial assumptions are realistic and well-justified
            """
        }
        
        return descriptions.get(asset_type, f"""
**Business Impact**: {asset_type.replace('_', ' ').title()} deliverable ready for use
**What to Review**: Content completeness, accuracy, and business relevance
**Quality Score**: {quality_score:.1%} ({len(quality_issues)} issues identified)
**Why Review Needed**: Ensure deliverable meets business requirements and quality standards
        """).strip()

    async def _has_duplicate_request(self, checkpoint: VerificationCheckpoint) -> bool:
        """Check if similar verification request already exists (legacy method)"""
        return await self._has_duplicate_request_enhanced(
            checkpoint.workspace_id, 
            checkpoint.task_id, 
            checkpoint.asset_type
        )
    
    async def _has_duplicate_request_enhanced(self, workspace_id: str, task_id: str, asset_type: str) -> bool:
        """Enhanced duplicate detection with multiple criteria"""
        
        try:
            from database import get_human_feedback_requests
            
            # Get pending requests for this workspace
            pending_requests = await get_human_feedback_requests(workspace_id, "pending")
            
            # Check for duplicates with enhanced criteria
            for request in pending_requests:
                request_context = request.get("context", {})
                
                # Enhanced matching criteria:
                # 1. Same asset type
                # 2. Same workspace 
                # 3. Recent creation (within 2 hours instead of 1)
                # 4. Check for task_id or similar verification context
                
                if request_context.get("asset_type") == asset_type:
                    # Check time window (extended to 2 hours for better detection)
                    from datetime import datetime, timedelta
                    created_time = request.get("created_at")
                    if created_time:
                        try:
                            created_dt = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
                            time_diff = datetime.now() - created_dt
                            
                            # Within 2 hours is considered duplicate
                            if time_diff < timedelta(hours=2):
                                # Additional checks for same asset type duplicates
                                if asset_type in ["contact_database", "email_sequence", "financial_plan"]:
                                    logger.info(f"🔄 ENHANCED DUPLICATE DETECTED: {asset_type} request exists within {time_diff}")
                                    return True
                                    
                                # For other assets, also check verification checkpoint ID or task context
                                if (request_context.get("verification_checkpoint_id") or 
                                    request_context.get("task_id") == task_id):
                                    logger.info(f"🔄 ENHANCED DUPLICATE DETECTED: Task or checkpoint match found")
                                    return True
                        except Exception as parse_error:
                            logger.debug(f"Error parsing date: {parse_error}")
                            continue
            
            return False
            
        except Exception as e:
            logger.error(f"Error in enhanced duplicate checking: {e}")
            return False

    def _create_deliverable_preview(self, deliverable_data: Dict[str, Any], max_items: int = 5) -> Dict[str, Any]:
        """Create a comprehensive preview of deliverable data for human review"""
        
        preview = {
            "content_for_review": {},
            "summary": {},
            "metadata": {}
        }
        
        try:
            # Skip technical metadata but show business content
            skip_keys = {"quality_validation", "enhancement_required", "task_metadata", "verification_required"}
            
            for key, value in deliverable_data.items():
                if key in skip_keys:
                    # Store metadata separately
                    preview["metadata"][key] = value
                    continue
                
                # Format content based on type for human-readable display
                if isinstance(value, list) and value:
                    # Show actual content of lists, especially for email sequences
                    preview["content_for_review"][key] = self._format_list_content(key, value, max_items)
                    preview["summary"][key] = f"Lista con {len(value)} elementi"
                    
                elif isinstance(value, dict) and value:
                    # Show formatted dict content
                    preview["content_for_review"][key] = self._format_dict_content(key, value, max_items)
                    preview["summary"][key] = f"Oggetto con {len(value)} proprietà"
                    
                elif isinstance(value, str) and value.strip():
                    # Show full text content for strings
                    if len(value) > 1000:
                        preview["content_for_review"][key] = value[:1000] + "\n\n... [contenuto troncato] ..."
                        preview["summary"][key] = f"Testo ({len(value)} caratteri, troncato)"
                    else:
                        preview["content_for_review"][key] = value
                        preview["summary"][key] = f"Testo ({len(value)} caratteri)"
                        
                elif value is not None:
                    preview["content_for_review"][key] = value
                    preview["summary"][key] = f"{type(value).__name__}: {str(value)[:50]}..."
            
            # If no content found, show a message
            if not preview["content_for_review"]:
                preview["content_for_review"]["note"] = "Nessun contenuto visibile trovato nel deliverable"
            
        except Exception as e:
            logger.error(f"Error creating deliverable preview: {e}")
            preview = {
                "content_for_review": {"error": "Errore nella creazione del preview"},
                "summary": {"error": str(e)},
                "metadata": {"original_keys": list(deliverable_data.keys())}
            }
        
        return preview
    
    def _format_list_content(self, key: str, items: list, max_items: int) -> Dict[str, Any]:
        """Format list content for human review"""
        
        formatted = {
            "total_count": len(items),
            "items": []
        }
        
        # Special formatting for email sequences
        if any(email_key in key.lower() for email_key in ["email", "sequence", "sequenz", "campaign"]):
            for i, item in enumerate(items[:max_items]):
                if isinstance(item, dict):
                    # Format email sequence item
                    email_preview = {}
                    if "subject" in item:
                        email_preview["subject"] = item["subject"]
                    if "body" in item:
                        email_preview["body"] = item["body"][:300] + "..." if len(str(item["body"])) > 300 else item["body"]
                    if "call_to_action" in item:
                        email_preview["call_to_action"] = item["call_to_action"]
                    if "send_delay" in item:
                        email_preview["timing"] = item["send_delay"]
                    
                    formatted["items"].append({
                        "sequence_number": i + 1,
                        "content": email_preview if email_preview else item
                    })
                else:
                    formatted["items"].append({
                        "sequence_number": i + 1,
                        "content": str(item)[:200] + "..." if len(str(item)) > 200 else str(item)
                    })
        
        # Special formatting for contacts
        elif any(contact_key in key.lower() for contact_key in ["contact", "contatt", "lead", "prospect"]):
            for i, item in enumerate(items[:max_items]):
                if isinstance(item, dict):
                    contact_preview = {}
                    if "name" in item:
                        contact_preview["name"] = item["name"]
                    if "email" in item:
                        contact_preview["email"] = item["email"]
                    if "company" in item:
                        contact_preview["company"] = item["company"]
                    if "role" in item or "job_title" in item:
                        contact_preview["role"] = item.get("role", item.get("job_title", ""))
                    
                    formatted["items"].append(contact_preview if contact_preview else item)
                else:
                    formatted["items"].append(str(item))
        
        # General list formatting
        else:
            for item in items[:max_items]:
                if isinstance(item, dict):
                    # Show key-value pairs for dict items
                    formatted["items"].append({k: str(v)[:100] + "..." if len(str(v)) > 100 else v for k, v in item.items()})
                else:
                    formatted["items"].append(str(item)[:200] + "..." if len(str(item)) > 200 else str(item))
        
        if len(items) > max_items:
            formatted["note"] = f"Mostrando {max_items} di {len(items)} elementi"
        
        return formatted
    
    def _format_dict_content(self, key: str, data: dict, max_items: int) -> Dict[str, Any]:
        """Format dict content for human review"""
        
        formatted = {}
        shown_items = 0
        
        for k, v in data.items():
            if shown_items >= max_items:
                break
                
            if isinstance(v, (str, int, float, bool)):
                if isinstance(v, str) and len(v) > 300:
                    formatted[k] = v[:300] + "..."
                else:
                    formatted[k] = v
            elif isinstance(v, list):
                formatted[k] = f"Lista con {len(v)} elementi: {str(v[:2])}..." if len(v) > 2 else v
            elif isinstance(v, dict):
                formatted[k] = f"Oggetto con {len(v)} proprietà: {list(v.keys())[:3]}..."
            else:
                formatted[k] = str(v)[:100] + "..." if len(str(v)) > 100 else str(v)
            
            shown_items += 1
        
        if len(data) > max_items:
            formatted["_note"] = f"Mostrando {max_items} di {len(data)} proprietà"
        
        return formatted
    
    async def process_verification_response(
        self,
        checkpoint_id: str,
        decision: str,
        feedback: str,
        reviewer_notes: Optional[str] = None
    ) -> bool:
        """
        ✅ PROCESS VERIFICATION RESPONSE - Handle human verification decision
        """
        
        try:
            checkpoint = self.verification_checkpoints.get(checkpoint_id)
            if not checkpoint:
                logger.error(f"Verification checkpoint {checkpoint_id} not found")
                return False
            
            # Update checkpoint with response
            checkpoint.reviewed_at = datetime.now().isoformat()
            checkpoint.reviewer_notes = reviewer_notes
            
            if decision.lower() == "approve":
                checkpoint.status = VerificationStatus.APPROVED
                checkpoint.approval_reason = feedback
                
                # Execute approval actions
                await self._execute_verification_actions(checkpoint.on_approval_actions)
                
                logger.info(f"✅ VERIFICATION APPROVED: Task {checkpoint.task_id} approved by human reviewer")
                
            elif decision.lower() == "reject":
                checkpoint.status = VerificationStatus.REJECTED
                checkpoint.rejection_reason = feedback
                
                # Execute rejection actions
                await self._execute_verification_actions(checkpoint.on_rejection_actions)
                
                logger.warning(f"❌ VERIFICATION REJECTED: Task {checkpoint.task_id} rejected - {feedback}")
                
            else:
                logger.error(f"Invalid verification decision: {decision}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing verification response: {e}", exc_info=True)
            return False
    
    async def _execute_verification_actions(self, actions: List[Dict[str, Any]]):
        """Execute actions based on verification decision"""
        
        from database import update_task_status, create_task, _update_goal_progress_from_task_completion
        
        for action in actions:
            try:
                action_type = action.get("type")
                
                if action_type == "update_task_status":
                    task_id = action.get("task_id")
                    status = action.get("status")
                    reason = action.get("reason", "")
                    
                    # Update task status
                    result = await update_task_status(task_id, status, {
                        "verification_result": reason,
                        "verification_timestamp": datetime.now().isoformat()
                    })
                    
                    logger.info(f"📝 TASK STATUS UPDATED: {task_id} -> {status} ({reason})")
                    
                elif action_type == "update_goal_progress":
                    task_id = action.get("task_id")
                    
                    # Get task to update goals
                    from database import get_task
                    task = await get_task(task_id)
                    if task and task.get("result"):
                        # Update goal progress
                        await _update_goal_progress_from_task_completion(task_id, task["result"])
                        logger.info(f"🎯 GOAL PROGRESS UPDATED: Task {task_id} progress applied to workspace goals")
                        
                        # Also trigger asset extraction for deliverable system
                        try:
                            from deliverable_system.concrete_asset_extractor import ConcreteAssetExtractor
                            asset_extractor = ConcreteAssetExtractor()
                            
                            # Extract assets from the verified task
                            extracted_assets = await asset_extractor.extract_from_task_result(
                                task_id=task_id,
                                task_result=task.get("result", {}),
                                task_name=task.get("name", ""),
                                workspace_id=task.get("workspace_id")
                            )
                            
                            if extracted_assets:
                                logger.info(f"📦 ASSET EXTRACTION: Extracted {len(extracted_assets)} assets from verified task {task_id}")
                            else:
                                logger.debug(f"📦 ASSET EXTRACTION: No assets extracted from verified task {task_id}")
                                
                        except Exception as asset_error:
                            logger.warning(f"Asset extraction failed for verified task {task_id}: {asset_error}")
                
                elif action_type == "create_enhancement_task":
                    # Create enhancement task for rejected deliverables
                    parent_task_id = action.get("parent_task_id")
                    task_name = action.get("task_name", "Enhance deliverable")
                    priority = action.get("priority", "medium")
                    
                    # Get parent task for context
                    from database import get_task
                    parent_task = await get_task(parent_task_id)
                    if parent_task:
                        workspace_id = parent_task.get("workspace_id")
                        
                        enhancement_task = await create_task(
                            workspace_id=workspace_id,
                            name=task_name,
                            status="pending",
                            priority=priority,
                            parent_task_id=parent_task_id,
                            description=f"Enhance deliverable based on human verification feedback",
                            created_by_task_id=parent_task_id,
                            creation_type="verification_enhancement"
                        )
                        
                        if enhancement_task:
                            logger.info(f"🔄 ENHANCEMENT TASK CREATED: {enhancement_task['id']} for rejected deliverable")
                
                elif action_type == "log_verification_result":
                    result = action.get("result")
                    task_id = action.get("task_id")
                    logger.info(f"📊 VERIFICATION LOGGED: Task {task_id} verification result: {result}")
                
            except Exception as action_error:
                logger.error(f"Error executing verification action {action}: {action_error}")
    
    async def cleanup_expired_checkpoints(self) -> int:
        """Clean up expired verification checkpoints"""
        
        expired_count = 0
        current_time = datetime.now()
        
        for checkpoint_id, checkpoint in list(self.verification_checkpoints.items()):
            try:
                expires_at = datetime.fromisoformat(checkpoint.expires_at.replace('Z', '+00:00'))
                
                if current_time > expires_at and checkpoint.status == VerificationStatus.PENDING:
                    # Mark as expired
                    checkpoint.status = VerificationStatus.EXPIRED
                    
                    # Execute rejection actions for expired checkpoints
                    await self._execute_verification_actions(checkpoint.on_rejection_actions)
                    
                    expired_count += 1
                    logger.warning(f"⏰ VERIFICATION EXPIRED: Checkpoint {checkpoint_id} expired after {checkpoint.timeout_hours}h")
                    
            except Exception as e:
                logger.error(f"Error processing expired checkpoint {checkpoint_id}: {e}")
        
        return expired_count
    
    def get_pending_verifications(self, workspace_id: Optional[str] = None) -> List[VerificationCheckpoint]:
        """Get pending verification checkpoints"""
        
        pending = [
            checkpoint for checkpoint in self.verification_checkpoints.values()
            if checkpoint.status == VerificationStatus.PENDING and
            (workspace_id is None or checkpoint.workspace_id == workspace_id)
        ]
        
        # Sort by priority and creation time
        priority_order = {
            VerificationPriority.CRITICAL: 0,
            VerificationPriority.HIGH: 1, 
            VerificationPriority.MEDIUM: 2,
            VerificationPriority.LOW: 3
        }
        
        pending.sort(key=lambda x: (priority_order.get(x.priority, 99), x.created_at))
        
        return pending
    
    def get_verification_stats(self) -> Dict[str, Any]:
        """Get verification system statistics"""
        
        total_checkpoints = len(self.verification_checkpoints)
        pending = len([c for c in self.verification_checkpoints.values() if c.status == VerificationStatus.PENDING])
        approved = len([c for c in self.verification_checkpoints.values() if c.status == VerificationStatus.APPROVED])
        rejected = len([c for c in self.verification_checkpoints.values() if c.status == VerificationStatus.REJECTED])
        expired = len([c for c in self.verification_checkpoints.values() if c.status == VerificationStatus.EXPIRED])
        
        return {
            "total_checkpoints": total_checkpoints,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "expired": expired,
            "approval_rate": (approved / max(total_checkpoints, 1)) * 100,
            "rejection_rate": (rejected / max(total_checkpoints, 1)) * 100
        }

# Singleton instance
human_verification_system = HumanVerificationSystem()