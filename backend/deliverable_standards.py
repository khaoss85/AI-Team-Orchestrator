#!/usr/bin/env python3

import logging
import json
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class DeliverableType(str, Enum):
    # 🌍 UNIVERSAL DELIVERABLE TYPES (not B2B/SaaS biased)
    CONTACT_DATABASE = "contact_database"  # Any contact collection
    EMAIL_SEQUENCE = "email_sequence"      # Any email communication
    CONTENT_CALENDAR = "content_calendar"  # Any content planning
    BUSINESS_ANALYSIS = "business_analysis" # Any business analysis
    STRATEGIC_PLAN = "strategic_plan"      # Any strategic planning
    FINANCIAL_PLAN = "financial_plan"      # Any financial planning
    TECHNICAL_DELIVERABLE = "technical_deliverable" # Any technical output
    PROCESS_DOCUMENT = "process_document"  # Any process documentation
    TRAINING_PROGRAM = "training_program"  # Educational/fitness/skill programs
    RESEARCH_REPORT = "research_report"    # Any research findings
    PROJECT_PROPOSAL = "project_proposal"  # Any project proposals
    DATA_ANALYSIS = "data_analysis"        # Any data analysis
    WORKFLOW_DESIGN = "workflow_design"    # Any workflow or process design
    RESOURCE_LIST = "resource_list"        # Any curated list of resources
    TEMPLATE_COLLECTION = "template_collection" # Any template or framework set
    GENERIC_DELIVERABLE = "generic_deliverable" # Universal fallback

class ValidationLevel(str, Enum):
    MINIMAL = "minimal"      # Basic structure check
    STANDARD = "standard"    # Full validation
    STRICT = "strict"        # Enhanced validation with business rules
    ENTERPRISE = "enterprise" # Full enterprise-grade validation

# === STRUCTURED OUTPUT MODELS ===

class ContactRecord(BaseModel):
    """Standard format for individual contact records"""
    name: str = Field(..., min_length=2, description="Full name of the contact")
    email: str = Field(..., regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', description="Valid email address")
    company: str = Field(..., min_length=2, description="Company name")
    role: Optional[str] = Field(None, description="Job title or role")
    phone: Optional[str] = Field(None, description="Phone number")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL")
    website: Optional[str] = Field(None, description="Company website")
    industry: Optional[str] = Field(None, description="Industry sector")
    company_size: Optional[str] = Field(None, description="Company size (e.g., '10-50 employees')")
    location: Optional[str] = Field(None, description="Geographic location")
    notes: Optional[str] = Field(None, description="Additional notes or context")
    source: Optional[str] = Field(None, description="How this contact was obtained")
    qualified: bool = Field(default=True, description="Whether contact meets ICP criteria")
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Last update timestamp")

    @validator('email')
    def validate_email_domain(cls, v):
        """Ensure email doesn't use common fake domains"""
        fake_domains = ['example.com', 'test.com', 'fake.com', 'dummy.com', 'placeholder.com']
        domain = v.split('@')[1].lower()
        if domain in fake_domains:
            raise ValueError(f"Fake email domain detected: {domain}")
        return v

    @validator('name')
    def validate_real_name(cls, v):
        """Check for obviously fake names"""
        fake_names = ['john doe', 'jane smith', 'test user', 'mario rossi', 'giuseppe verdi']
        if v.lower().strip() in fake_names:
            raise ValueError(f"Fake name detected: {v}")
        return v

class ContactDatabase(BaseModel):
    """Standard format for contact database deliverables"""
    contacts: List[ContactRecord] = Field(..., min_items=1, description="List of contact records")
    total_contacts: int = Field(..., ge=0, description="Total number of contacts")
    icp_criteria: Dict[str, Any] = Field(..., description="Ideal Customer Profile criteria used")
    data_sources: List[str] = Field(..., description="Sources where contacts were obtained")
    collection_method: str = Field(..., description="Method used to collect contacts")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Overall quality score")
    verification_status: str = Field(default="unverified", description="Email verification status")
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    @validator('total_contacts')
    def validate_contact_count(cls, v, values):
        """Ensure total_contacts matches actual contact count"""
        if 'contacts' in values and len(values['contacts']) != v:
            raise ValueError(f"total_contacts ({v}) doesn't match actual contacts ({len(values['contacts'])})")
        return v

class EmailMessage(BaseModel):
    """Standard format for individual email messages"""
    subject_line: str = Field(..., min_length=5, max_length=150, description="Email subject line")
    email_body: str = Field(..., min_length=50, description="Email message content")
    call_to_action: str = Field(..., min_length=5, description="Primary call-to-action")
    personalization_fields: List[str] = Field(default_factory=list, description="Fields to personalize")
    send_delay_days: int = Field(default=0, ge=0, description="Days to wait before sending")
    email_type: str = Field(default="outreach", description="Type of email (outreach, follow-up, etc.)")
    estimated_reading_time: Optional[int] = Field(None, description="Estimated reading time in seconds")
    
    @validator('subject_line')
    def validate_subject_line(cls, v):
        """Ensure subject line is not generic"""
        generic_subjects = ['hello', 'test', 'subject', 'email']
        if v.lower().strip() in generic_subjects:
            raise ValueError(f"Generic subject line: {v}")
        return v

class EmailSequence(BaseModel):
    """Standard format for email sequence deliverables"""
    sequence_name: str = Field(..., min_length=5, description="Name of the email sequence")
    target_audience: str = Field(..., description="Target audience description")
    sequence_goal: str = Field(..., description="Primary goal of the sequence")
    emails: List[EmailMessage] = Field(..., min_items=1, description="Email messages in sequence")
    total_emails: int = Field(..., ge=1, description="Total number of emails")
    estimated_duration_days: int = Field(..., ge=1, description="Total sequence duration")
    expected_open_rate: Optional[float] = Field(None, ge=0.0, le=1.0, description="Expected open rate")
    expected_click_rate: Optional[float] = Field(None, ge=0.0, le=1.0, description="Expected click-through rate")
    platform_compatibility: List[str] = Field(default_factory=list, description="Compatible email platforms")
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    @validator('total_emails')
    def validate_email_count(cls, v, values):
        """Ensure total_emails matches actual email count"""
        if 'emails' in values and len(values['emails']) != v:
            raise ValueError(f"total_emails ({v}) doesn't match actual emails ({len(values['emails'])})")
        return v

class ContentPiece(BaseModel):
    """Standard format for individual content pieces"""
    title: str = Field(..., min_length=5, description="Content title")
    content_type: str = Field(..., description="Type of content (post, article, video, etc.)")
    platform: str = Field(..., description="Target platform")
    content_body: str = Field(..., min_length=20, description="Main content text")
    hashtags: List[str] = Field(default_factory=list, description="Relevant hashtags")
    posting_date: Optional[str] = Field(None, description="Scheduled posting date")
    target_audience: Optional[str] = Field(None, description="Target audience")
    call_to_action: Optional[str] = Field(None, description="Call-to-action")
    estimated_reach: Optional[int] = Field(None, ge=0, description="Estimated reach")
    media_requirements: List[str] = Field(default_factory=list, description="Required media assets")

class ContentCalendar(BaseModel):
    """Standard format for content calendar deliverables"""
    calendar_name: str = Field(..., min_length=5, description="Name of the content calendar")
    time_period: str = Field(..., description="Time period covered (e.g., 'Q1 2024', 'January 2024')")
    platforms: List[str] = Field(..., min_items=1, description="Target platforms")
    content_pieces: List[ContentPiece] = Field(..., min_items=1, description="Content pieces")
    total_pieces: int = Field(..., ge=1, description="Total number of content pieces")
    posting_frequency: str = Field(..., description="Posting frequency")
    content_themes: List[str] = Field(default_factory=list, description="Main content themes")
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat())

class BusinessInsight(BaseModel):
    """Standard format for business insights"""
    insight_title: str = Field(..., min_length=5, description="Title of the insight")
    category: str = Field(..., description="Category (market, competitor, customer, etc.)")
    description: str = Field(..., min_length=20, description="Detailed description")
    data_source: str = Field(..., description="Source of data for this insight")
    confidence_level: float = Field(..., ge=0.0, le=1.0, description="Confidence in the insight")
    business_impact: str = Field(..., description="Potential business impact")
    recommended_actions: List[str] = Field(..., min_items=1, description="Recommended actions")
    priority: str = Field(default="medium", description="Priority level")

class BusinessAnalysis(BaseModel):
    """Standard format for business analysis deliverables"""
    analysis_title: str = Field(..., min_length=5, description="Title of the analysis")
    analysis_type: str = Field(..., description="Type of analysis (competitor, market, SWOT, etc.)")
    executive_summary: str = Field(..., min_length=100, description="Executive summary")
    key_insights: List[BusinessInsight] = Field(..., min_items=1, description="Key business insights")
    methodology: str = Field(..., description="Analysis methodology used")
    data_sources: List[str] = Field(..., min_items=1, description="Data sources used")
    recommendations: List[str] = Field(..., min_items=1, description="Strategic recommendations")
    next_steps: List[str] = Field(..., min_items=1, description="Recommended next steps")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall confidence in analysis")
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat())

class StrategicPlan(BaseModel):
    """Standard format for strategic plan deliverables"""
    plan_title: str = Field(..., min_length=5, description="Title of the strategic plan")
    planning_horizon: str = Field(..., description="Time horizon (e.g., '12 months', 'Q1-Q2 2024')")
    objectives: List[str] = Field(..., min_items=1, description="Strategic objectives")
    key_initiatives: List[Dict[str, Any]] = Field(..., min_items=1, description="Key initiatives with details")
    success_metrics: List[Dict[str, Any]] = Field(..., min_items=1, description="Success metrics and KPIs")
    resource_requirements: Dict[str, Any] = Field(..., description="Required resources")
    timeline: Dict[str, Any] = Field(..., description="Implementation timeline")
    risk_assessment: List[Dict[str, Any]] = Field(default_factory=list, description="Risk assessment")
    budget_estimate: Optional[Dict[str, Any]] = Field(None, description="Budget estimates")
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat())

class FinancialPlan(BaseModel):
    """Standard format for financial plan deliverables"""
    plan_title: str = Field(..., min_length=5, description="Title of the financial plan")
    planning_period: str = Field(..., description="Planning period")
    revenue_projections: Dict[str, Any] = Field(..., description="Revenue projections")
    cost_structure: Dict[str, Any] = Field(..., description="Cost structure breakdown")
    profit_projections: Dict[str, Any] = Field(..., description="Profit projections")
    cash_flow: Dict[str, Any] = Field(..., description="Cash flow projections")
    key_assumptions: List[str] = Field(..., min_items=1, description="Key financial assumptions")
    sensitivity_analysis: Optional[Dict[str, Any]] = Field(None, description="Sensitivity analysis")
    break_even_analysis: Optional[Dict[str, Any]] = Field(None, description="Break-even analysis")
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat())

# === DELIVERABLE STANDARDS SYSTEM ===

class DeliverableStandards:
    """
    📋 DELIVERABLE STANDARDS SYSTEM - Enforces structured output requirements
    
    This system defines and validates structured output formats for each deliverable type,
    ensuring consistent, actionable, and business-ready outputs.
    """
    
    def __init__(self):
        # Map deliverable types to their standard models
        self.standard_models = {
            DeliverableType.CONTACT_DATABASE: ContactDatabase,
            DeliverableType.EMAIL_SEQUENCE: EmailSequence,
            DeliverableType.CONTENT_CALENDAR: ContentCalendar,
            DeliverableType.BUSINESS_ANALYSIS: BusinessAnalysis,
            DeliverableType.STRATEGIC_PLAN: StrategicPlan,
            DeliverableType.FINANCIAL_PLAN: FinancialPlan,
        }
        
        # Validation rules for each type
        self.validation_rules = {
            DeliverableType.CONTACT_DATABASE: {
                "min_contacts": 1,
                "require_email_validation": True,
                "require_icp_criteria": True,
                "max_fake_threshold": 0.1  # Max 10% fake/invalid contacts
            },
            DeliverableType.EMAIL_SEQUENCE: {
                "min_emails": 1,
                "max_emails": 20,
                "require_cta": True,
                "min_subject_length": 5,
                "min_body_length": 50
            },
            DeliverableType.CONTENT_CALENDAR: {
                "min_content_pieces": 1,
                "require_scheduling": False,
                "require_hashtags": False,
                "min_platforms": 1
            },
            DeliverableType.BUSINESS_ANALYSIS: {
                "min_insights": 1,
                "require_data_sources": True,
                "require_recommendations": True,
                "min_confidence": 0.6
            }
        }
        
        # Common business rules
        self.business_rules = {
            "no_fake_data": True,
            "require_real_contacts": True,
            "validate_email_domains": True,
            "check_placeholder_content": True,
            "ensure_actionable_outputs": True
        }
    
    def get_standard_format(self, deliverable_type: str) -> Optional[type]:
        """Get the standard Pydantic model for a deliverable type"""
        
        try:
            delivery_type_enum = DeliverableType(deliverable_type.lower())
            return self.standard_models.get(delivery_type_enum)
        except (ValueError, KeyError):
            logger.warning(f"No standard format defined for deliverable type: {deliverable_type}")
            return None
    
    def validate_deliverable(
        self,
        deliverable_data: Dict[str, Any],
        deliverable_type: str,
        validation_level: ValidationLevel = ValidationLevel.STANDARD
    ) -> Tuple[bool, List[str], Optional[Any]]:
        """
        🔍 VALIDATE DELIVERABLE - Validates deliverable against standards
        
        Returns:
            Tuple of (is_valid, error_messages, validated_model)
        """
        
        errors = []
        validated_model = None
        
        try:
            # Get standard model for this deliverable type
            model_class = self.get_standard_format(deliverable_type)
            
            if not model_class:
                errors.append(f"No standard format defined for type: {deliverable_type}")
                return False, errors, None
            
            # Attempt to validate using Pydantic model
            try:
                validated_model = model_class(**deliverable_data)
                logger.info(f"✅ STRUCTURE VALIDATION PASSED: {deliverable_type}")
                
            except Exception as e:
                errors.append(f"Structure validation failed: {str(e)}")
                logger.warning(f"🔴 STRUCTURE VALIDATION FAILED: {deliverable_type} - {str(e)}")
                
                # For standard+ validation levels, structure failure is critical
                if validation_level in [ValidationLevel.STANDARD, ValidationLevel.STRICT, ValidationLevel.ENTERPRISE]:
                    return False, errors, None
            
            # Apply business rule validation
            if validation_level in [ValidationLevel.STRICT, ValidationLevel.ENTERPRISE]:
                business_errors = self._validate_business_rules(deliverable_data, deliverable_type)
                errors.extend(business_errors)
            
            # Apply domain-specific validation
            domain_errors = self._validate_domain_specific_rules(deliverable_data, deliverable_type, validation_level)
            errors.extend(domain_errors)
            
            # Determine overall validation result
            is_valid = len(errors) == 0
            
            if is_valid:
                logger.info(f"✅ DELIVERABLE VALIDATION PASSED: {deliverable_type} ({validation_level.value} level)")
            else:
                logger.warning(f"🔴 DELIVERABLE VALIDATION FAILED: {deliverable_type} - {len(errors)} errors")
            
            return is_valid, errors, validated_model
            
        except Exception as e:
            logger.error(f"Error during deliverable validation: {e}", exc_info=True)
            errors.append(f"Validation system error: {str(e)}")
            return False, errors, None
    
    def _validate_business_rules(self, data: Dict[str, Any], deliverable_type: str) -> List[str]:
        """Apply general business rules validation"""
        
        errors = []
        data_str = json.dumps(data, default=str).lower()
        
        # Check for fake/placeholder content
        if self.business_rules.get("no_fake_data"):
            fake_indicators = [
                "john doe", "jane smith", "example.com", "test@", "placeholder",
                "lorem ipsum", "sample data", "fake", "dummy", "mario rossi"
            ]
            
            for indicator in fake_indicators:
                if indicator in data_str:
                    errors.append(f"Fake/placeholder content detected: '{indicator}'")
        
        # Check for placeholder fields
        if self.business_rules.get("check_placeholder_content"):
            placeholder_patterns = [
                "[placeholder]", "{placeholder}", "<placeholder>", "your company",
                "insert here", "add your", "customize this", "fill in"
            ]
            
            for pattern in placeholder_patterns:
                if pattern in data_str:
                    errors.append(f"Placeholder content not replaced: '{pattern}'")
        
        # Validate email domains for contact-related deliverables
        if deliverable_type == "contact_database" and self.business_rules.get("validate_email_domains"):
            contacts = data.get("contacts", [])
            if isinstance(contacts, list):
                fake_domains = ["example.com", "test.com", "fake.com", "dummy.com"]
                for contact in contacts:
                    if isinstance(contact, dict) and "email" in contact:
                        email = contact["email"]
                        if "@" in email:
                            domain = email.split("@")[1].lower()
                            if domain in fake_domains:
                                errors.append(f"Fake email domain in contact: {email}")
        
        return errors
    
    def _validate_domain_specific_rules(
        self, 
        data: Dict[str, Any], 
        deliverable_type: str,
        validation_level: ValidationLevel
    ) -> List[str]:
        """Apply domain-specific validation rules"""
        
        errors = []
        rules = self.validation_rules.get(DeliverableType(deliverable_type), {})
        
        try:
            if deliverable_type == "contact_database":
                contacts = data.get("contacts", [])
                
                # Check minimum contacts
                min_contacts = rules.get("min_contacts", 1)
                if len(contacts) < min_contacts:
                    errors.append(f"Insufficient contacts: {len(contacts)} < {min_contacts}")
                
                # Check for required ICP criteria
                if rules.get("require_icp_criteria") and not data.get("icp_criteria"):
                    errors.append("Missing ICP criteria definition")
                
                # Check fake contact threshold
                max_fake_threshold = rules.get("max_fake_threshold", 0.1)
                fake_count = self._count_fake_contacts(contacts)
                fake_ratio = fake_count / max(len(contacts), 1)
                
                if fake_ratio > max_fake_threshold:
                    errors.append(f"Too many fake contacts: {fake_ratio:.1%} > {max_fake_threshold:.1%}")
            
            elif deliverable_type == "email_sequence":
                emails = data.get("emails", [])
                
                # Check email count limits
                min_emails = rules.get("min_emails", 1)
                max_emails = rules.get("max_emails", 20)
                
                if len(emails) < min_emails:
                    errors.append(f"Too few emails: {len(emails)} < {min_emails}")
                elif len(emails) > max_emails:
                    errors.append(f"Too many emails: {len(emails)} > {max_emails}")
                
                # Check email content quality
                for i, email in enumerate(emails):
                    if isinstance(email, dict):
                        subject = email.get("subject_line", "")
                        body = email.get("email_body", "")
                        
                        if len(subject) < rules.get("min_subject_length", 5):
                            errors.append(f"Email {i+1} subject too short: {len(subject)} chars")
                        
                        if len(body) < rules.get("min_body_length", 50):
                            errors.append(f"Email {i+1} body too short: {len(body)} chars")
                        
                        if rules.get("require_cta") and not email.get("call_to_action"):
                            errors.append(f"Email {i+1} missing call-to-action")
            
            elif deliverable_type == "business_analysis":
                insights = data.get("key_insights", [])
                
                # Check minimum insights
                min_insights = rules.get("min_insights", 1)
                if len(insights) < min_insights:
                    errors.append(f"Insufficient insights: {len(insights)} < {min_insights}")
                
                # Check data sources
                if rules.get("require_data_sources") and not data.get("data_sources"):
                    errors.append("Missing data sources documentation")
                
                # Check recommendations
                if rules.get("require_recommendations") and not data.get("recommendations"):
                    errors.append("Missing business recommendations")
                
                # Check confidence level
                min_confidence = rules.get("min_confidence", 0.6)
                confidence = data.get("confidence_score", 0.0)
                if confidence < min_confidence:
                    errors.append(f"Low confidence score: {confidence:.1%} < {min_confidence:.1%}")
            
        except Exception as e:
            logger.error(f"Error in domain-specific validation: {e}")
            errors.append(f"Domain validation error: {str(e)}")
        
        return errors
    
    def _count_fake_contacts(self, contacts: List[Dict[str, Any]]) -> int:
        """Count obviously fake contacts in a contact list"""
        
        fake_count = 0
        fake_names = ["john doe", "jane smith", "test user", "mario rossi", "giuseppe verdi"]
        fake_domains = ["example.com", "test.com", "fake.com", "dummy.com"]
        
        for contact in contacts:
            if not isinstance(contact, dict):
                continue
                
            name = contact.get("name", "").lower().strip()
            email = contact.get("email", "").lower().strip()
            
            # Check for fake names
            if name in fake_names:
                fake_count += 1
                continue
            
            # Check for fake email domains
            if "@" in email:
                domain = email.split("@")[1]
                if domain in fake_domains:
                    fake_count += 1
                    continue
        
        return fake_count
    
    def generate_template(self, deliverable_type: str) -> Dict[str, Any]:
        """
        📋 GENERATE TEMPLATE - Creates a structured template for a deliverable type
        """
        
        model_class = self.get_standard_format(deliverable_type)
        if not model_class:
            return {"error": f"No template available for type: {deliverable_type}"}
        
        try:
            # Create example data based on the model schema
            schema = model_class.schema()
            template = self._generate_template_from_schema(schema, deliverable_type)
            
            return {
                "deliverable_type": deliverable_type,
                "template": template,
                "schema": schema,
                "instructions": self._get_template_instructions(deliverable_type),
                "validation_rules": self.validation_rules.get(DeliverableType(deliverable_type), {}),
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating template for {deliverable_type}: {e}")
            return {"error": f"Template generation failed: {str(e)}"}
    
    def _generate_template_from_schema(self, schema: Dict[str, Any], deliverable_type: str) -> Dict[str, Any]:
        """Generate template data from Pydantic schema"""
        
        template = {}
        properties = schema.get("properties", {})
        
        for field_name, field_info in properties.items():
            field_type = field_info.get("type")
            field_format = field_info.get("format")
            
            if field_type == "string":
                if field_format == "date-time":
                    template[field_name] = datetime.now().isoformat()
                elif "email" in field_name.lower():
                    template[field_name] = "contact@company.com"
                elif "name" in field_name.lower():
                    template[field_name] = "Professional Name"
                else:
                    template[field_name] = f"[{field_info.get('description', field_name)}]"
            
            elif field_type == "integer":
                template[field_name] = 0
            
            elif field_type == "number":
                template[field_name] = 0.0
            
            elif field_type == "boolean":
                template[field_name] = True
            
            elif field_type == "array":
                items_type = field_info.get("items", {}).get("type", "string")
                if items_type == "object":
                    template[field_name] = [{}]
                else:
                    template[field_name] = [f"[{field_info.get('description', 'item')}]"]
            
            elif field_type == "object":
                template[field_name] = {}
        
        return template
    
    def _get_template_instructions(self, deliverable_type: str) -> List[str]:
        """Get specific instructions for each deliverable type"""
        
        instructions = {
            "contact_database": [
                "Replace all placeholder contact information with real, verified business contacts",
                "Ensure all email addresses are valid and belong to real professionals",
                "Include complete company information for each contact",
                "Verify contacts match your Ideal Customer Profile (ICP) criteria",
                "Remove any duplicate or invalid entries"
            ],
            "email_sequence": [
                "Create compelling, personalized subject lines for each email",
                "Write professional email content appropriate for your target audience",
                "Include clear call-to-actions in each email",
                "Set appropriate sending delays between emails",
                "Ensure emails follow a logical progression"
            ],
            "content_calendar": [
                "Plan content for specific dates and platforms",
                "Include engaging content titles and descriptions",
                "Add relevant hashtags for each platform",
                "Specify target audience for each piece",
                "Include media requirements (images, videos, etc.)"
            ],
            "business_analysis": [
                "Base insights on real market data and research",
                "Provide specific, actionable recommendations",
                "Include confidence levels for each insight",
                "Document all data sources used",
                "Ensure analysis is relevant to business context"
            ]
        }
        
        return instructions.get(deliverable_type, [
            "Follow the structured format exactly as specified",
            "Replace all placeholder content with real, actionable information", 
            "Ensure all data is accurate and verified",
            "Make outputs immediately usable for business purposes"
        ])
    
    def get_validation_summary(
        self,
        deliverable_type: str,
        validation_level: ValidationLevel = ValidationLevel.STANDARD
    ) -> Dict[str, Any]:
        """Get validation requirements summary for a deliverable type"""
        
        model_class = self.get_standard_format(deliverable_type)
        rules = self.validation_rules.get(DeliverableType(deliverable_type), {})
        
        return {
            "deliverable_type": deliverable_type,
            "validation_level": validation_level.value,
            "has_standard_model": model_class is not None,
            "model_name": model_class.__name__ if model_class else None,
            "validation_rules": rules,
            "business_rules_applied": list(self.business_rules.keys()),
            "required_fields": self._get_required_fields(model_class) if model_class else [],
            "optional_fields": self._get_optional_fields(model_class) if model_class else []
        }
    
    def _get_required_fields(self, model_class) -> List[str]:
        """Extract required fields from Pydantic model"""
        if not model_class:
            return []
        
        schema = model_class.schema()
        required = schema.get("required", [])
        return required
    
    def _get_optional_fields(self, model_class) -> List[str]:
        """Extract optional fields from Pydantic model"""
        if not model_class:
            return []
        
        schema = model_class.schema()
        all_fields = set(schema.get("properties", {}).keys())
        required_fields = set(schema.get("required", []))
        optional_fields = all_fields - required_fields
        return list(optional_fields)

# Singleton instance
deliverable_standards = DeliverableStandards()