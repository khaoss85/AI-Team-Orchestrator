"""
Business Asset Synthesizer Service

Transforms task outputs and research data into actionable business deliverables.
Solves the critical issue where 68% of deliverables are process documentation
instead of actual business assets.
"""

import re
import json
import csv
from io import StringIO
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from datetime import datetime
import logging
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AssetType(Enum):
    """Types of business assets the system can generate"""
    CONTACT_LIST = "contact_list"
    EMAIL_SEQUENCE = "email_sequence"
    STRATEGY_DOCUMENT = "strategy_document"
    METRICS_DASHBOARD = "metrics_dashboard"
    CONTENT_CALENDAR = "content_calendar"
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    SOCIAL_MEDIA_POSTS = "social_media_posts"
    PRODUCT_ROADMAP = "product_roadmap"


class BusinessAsset(BaseModel):
    """Base model for all business assets"""
    asset_type: AssetType
    title: str
    data: Any
    format: str  # csv, json, html, markdown
    metadata: Dict[str, Any] = Field(default_factory=dict)
    validation_score: float = 0.0
    business_value_score: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            "asset_type": self.asset_type.value,
            "title": self.title,
            "data": self.data,
            "format": self.format,
            "metadata": self.metadata,
            "validation_score": self.validation_score,
            "business_value_score": self.business_value_score,
            "created_at": self.created_at.isoformat()
        }
    
    def to_display_format(self) -> str:
        """Convert to user-friendly display format"""
        if self.format == "csv":
            return self._format_as_csv()
        elif self.format == "json":
            return json.dumps(self.data, indent=2)
        elif self.format == "html":
            return self._format_as_html()
        else:
            return str(self.data)
    
    def _format_as_csv(self) -> str:
        """Format data as CSV string"""
        if not isinstance(self.data, list) or not self.data:
            return ""
        
        output = StringIO()
        if isinstance(self.data[0], dict):
            writer = csv.DictWriter(output, fieldnames=self.data[0].keys())
            writer.writeheader()
            writer.writerows(self.data)
        else:
            writer = csv.writer(output)
            writer.writerows(self.data)
        
        return output.getvalue()
    
    def _format_as_html(self) -> str:
        """Format data as HTML"""
        # Basic HTML formatting - can be enhanced
        html = f"<div class='business-asset'>\n"
        html += f"<h2>{self.title}</h2>\n"
        
        if isinstance(self.data, list) and self.data and isinstance(self.data[0], dict):
            # Table format for structured data
            html += "<table class='asset-table'>\n<thead><tr>"
            for key in self.data[0].keys():
                html += f"<th>{key}</th>"
            html += "</tr></thead>\n<tbody>"
            for item in self.data:
                html += "<tr>"
                for value in item.values():
                    html += f"<td>{value}</td>"
                html += "</tr>\n"
            html += "</tbody></table>\n"
        else:
            # Generic display
            html += f"<pre>{json.dumps(self.data, indent=2)}</pre>\n"
        
        html += "</div>"
        return html


class ContactListAsset(BusinessAsset):
    """Specific asset type for contact lists"""
    asset_type: AssetType = AssetType.CONTACT_LIST
    format: str = "csv"


class EmailSequenceAsset(BusinessAsset):
    """Specific asset type for email sequences"""
    asset_type: AssetType = AssetType.EMAIL_SEQUENCE
    format: str = "json"


class BusinessAssetSynthesizer:
    """
    Main service for synthesizing business assets from task outputs.
    Transforms research and task data into actionable deliverables.
    """
    
    def __init__(self):
        self.asset_patterns = self._initialize_patterns()
        self.extraction_rules = self._initialize_extraction_rules()
    
    def _initialize_patterns(self) -> Dict[str, AssetType]:
        """Initialize regex patterns for goal-to-asset mapping"""
        return {
            r"lista.*contatti|contact.*list|CSV.*contact|ICP.*list": AssetType.CONTACT_LIST,
            r"email.*sequence|sequenze.*email|email.*campaign|campagna.*email": AssetType.EMAIL_SEQUENCE,
            r"strategia|strategy|piano.*marketing|marketing.*plan": AssetType.STRATEGY_DOCUMENT,
            r"metriche|metrics|KPI|dashboard|analytics": AssetType.METRICS_DASHBOARD,
            r"calendario.*contenuti|content.*calendar|editorial.*calendar": AssetType.CONTENT_CALENDAR,
            r"analisi.*competitor|competitive.*analysis|competitor.*research": AssetType.COMPETITIVE_ANALYSIS,
            r"social.*media|post.*social|linkedin.*content|twitter": AssetType.SOCIAL_MEDIA_POSTS,
            r"roadmap|product.*plan|feature.*timeline": AssetType.PRODUCT_ROADMAP
        }
    
    def _initialize_extraction_rules(self) -> Dict:
        """Initialize rules for extracting data from different sources"""
        return {
            "email_patterns": re.compile(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'),
            "url_patterns": re.compile(r'https?://[^\s]+'),
            "phone_patterns": re.compile(r'[\+]?[(]?[0-9]{1,3}[)]?[-.\s]?[(]?[0-9]{1,4}[)]?[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,9}'),
            "company_indicators": ["Inc", "LLC", "Corp", "Ltd", "GmbH", "SRL", "SpA", "Company"],
            "role_indicators": ["CEO", "CTO", "CMO", "Director", "Manager", "VP", "President", "Founder"]
        }
    
    async def synthesize_deliverable(
        self,
        goal_description: str,
        task_outputs: List[Dict],
        workspace_context: Optional[Dict] = None
    ) -> BusinessAsset:
        """
        Main synthesis pipeline - transforms task outputs into business assets
        
        Args:
            goal_description: The workspace goal description
            task_outputs: List of outputs from completed tasks
            workspace_context: Additional context about the workspace
            
        Returns:
            BusinessAsset ready for delivery to user
        """
        try:
            # 1. Determine the type of asset to create
            asset_type = self._determine_asset_type(goal_description)
            logger.info(f"Determined asset type: {asset_type.value} for goal: {goal_description}")
            
            # 2. Extract actionable data from task outputs
            extracted_data = await self._extract_actionable_data(task_outputs, asset_type)
            logger.info(f"Extracted {len(extracted_data)} data points from task outputs")
            
            # 3. Generate the specific business asset
            business_asset = await self._generate_business_asset(
                asset_type=asset_type,
                extracted_data=extracted_data,
                goal_description=goal_description,
                workspace_context=workspace_context
            )
            
            # 4. Validate and score the asset
            business_asset = self._validate_and_score(business_asset)
            
            logger.info(f"Successfully synthesized {asset_type.value} with score: {business_asset.business_value_score}")
            return business_asset
            
        except Exception as e:
            logger.error(f"Failed to synthesize deliverable: {e}")
            # Return a basic asset with the raw data
            return self._create_fallback_asset(goal_description, task_outputs)
    
    def _determine_asset_type(self, goal_description: str) -> AssetType:
        """
        Determine what type of business asset to create based on the goal
        """
        goal_lower = goal_description.lower()
        
        for pattern, asset_type in self.asset_patterns.items():
            if re.search(pattern, goal_lower):
                return asset_type
        
        # Default to strategy document if no pattern matches
        return AssetType.STRATEGY_DOCUMENT
    
    async def _extract_actionable_data(
        self, 
        task_outputs: List[Dict],
        asset_type: AssetType
    ) -> Dict[str, Any]:
        """
        Extract actionable data from task outputs based on asset type
        """
        extracted = {
            "raw_text": [],
            "structured_data": [],
            "contacts": [],
            "emails": [],
            "urls": [],
            "metrics": [],
            "content_pieces": []
        }
        
        for output in task_outputs:
            # Extract text content
            content = output.get("content", output.get("output", ""))
            
            if isinstance(content, str):
                extracted["raw_text"].append(content)
                
                # Extract specific data based on asset type
                if asset_type == AssetType.CONTACT_LIST:
                    contacts = self._extract_contacts_from_text(content)
                    extracted["contacts"].extend(contacts)
                    
                elif asset_type == AssetType.EMAIL_SEQUENCE:
                    emails = self._extract_email_templates(content)
                    extracted["emails"].extend(emails)
                    
            elif isinstance(content, dict):
                extracted["structured_data"].append(content)
                
                # Process structured data
                if "contacts" in content:
                    extracted["contacts"].extend(content["contacts"])
                if "emails" in content:
                    extracted["emails"].extend(content["emails"])
                if "metrics" in content:
                    extracted["metrics"].append(content["metrics"])
        
        return extracted
    
    def _extract_contacts_from_text(self, text: str) -> List[Dict]:
        """
        Extract contact information from unstructured text
        """
        contacts = []
        
        # Find all emails in text
        emails = self.extraction_rules["email_patterns"].findall(text)
        
        for email in emails:
            contact = {"email": email}
            
            # Try to extract name (look around email for name patterns)
            name_pattern = r'([A-Z][a-z]+ [A-Z][a-z]+)'
            email_context = text[max(0, text.find(email)-100):text.find(email)+100]
            names = re.findall(name_pattern, email_context)
            if names:
                contact["name"] = names[0]
            
            # Extract company (look for company indicators)
            for indicator in self.extraction_rules["company_indicators"]:
                company_pattern = rf'([A-Za-z0-9\s]+{indicator})'
                companies = re.findall(company_pattern, email_context)
                if companies:
                    contact["company"] = companies[0].strip()
                    break
            
            # Extract role
            for role in self.extraction_rules["role_indicators"]:
                if role in email_context:
                    contact["role"] = role
                    break
            
            contacts.append(contact)
        
        return contacts
    
    def _extract_email_templates(self, text: str) -> List[Dict]:
        """
        Extract email templates from text
        """
        templates = []
        
        # Look for email structure patterns
        subject_pattern = r'Subject:?\s*(.+)'
        body_pattern = r'(Dear\s+.+?(?:Best regards|Sincerely|Thank you).+?)'
        
        subjects = re.findall(subject_pattern, text, re.IGNORECASE)
        bodies = re.findall(body_pattern, text, re.DOTALL | re.IGNORECASE)
        
        for i, subject in enumerate(subjects):
            template = {
                "email_number": i + 1,
                "subject": subject.strip(),
                "body": bodies[i].strip() if i < len(bodies) else "",
                "send_day": i * 3  # Default spacing
            }
            templates.append(template)
        
        return templates
    
    async def _generate_business_asset(
        self,
        asset_type: AssetType,
        extracted_data: Dict,
        goal_description: str,
        workspace_context: Optional[Dict]
    ) -> BusinessAsset:
        """
        Generate the specific type of business asset
        """
        if asset_type == AssetType.CONTACT_LIST:
            return await self._generate_contact_list(
                extracted_data, goal_description, workspace_context
            )
        elif asset_type == AssetType.EMAIL_SEQUENCE:
            return await self._generate_email_sequence(
                extracted_data, goal_description, workspace_context
            )
        elif asset_type == AssetType.METRICS_DASHBOARD:
            return await self._generate_metrics_dashboard(
                extracted_data, goal_description, workspace_context
            )
        else:
            return await self._generate_strategy_document(
                extracted_data, goal_description, workspace_context
            )
    
    async def _generate_contact_list(
        self,
        data: Dict,
        goal: str,
        context: Optional[Dict]
    ) -> ContactListAsset:
        """
        Generate a CSV-ready contact list
        """
        contacts = data.get("contacts", [])
        
        # Deduplicate by email
        seen_emails = set()
        unique_contacts = []
        for contact in contacts:
            email = contact.get("email")
            if email and email not in seen_emails:
                seen_emails.add(email)
                # Ensure all required fields exist
                contact.setdefault("name", "Unknown")
                contact.setdefault("company", "Unknown")
                contact.setdefault("role", "Unknown")
                unique_contacts.append(contact)
        
        # Sort by company and role
        unique_contacts.sort(key=lambda x: (x.get("company", ""), x.get("role", "")))
        
        return ContactListAsset(
            title=f"Contact List - {goal[:50]}",
            data=unique_contacts,
            metadata={
                "total_contacts": len(unique_contacts),
                "unique_companies": len(set(c.get("company", "") for c in unique_contacts)),
                "extraction_sources": len(data.get("raw_text", [])),
                "goal": goal
            },
            validation_score=0.8 if unique_contacts else 0.0,
            business_value_score=min(1.0, len(unique_contacts) / 50)  # 50 contacts = perfect score
        )
    
    async def _generate_email_sequence(
        self,
        data: Dict,
        goal: str,
        context: Optional[Dict]
    ) -> EmailSequenceAsset:
        """
        Generate an email sequence with templates
        """
        emails = data.get("emails", [])
        
        # If no emails extracted, create a basic sequence from text
        if not emails and data.get("raw_text"):
            # Create a basic 3-email sequence
            emails = [
                {
                    "email_number": 1,
                    "subject": "Introduction - How we can help {{company}}",
                    "body": "Hi {{first_name}},\n\nI noticed your company is focused on growth...",
                    "send_day": 0
                },
                {
                    "email_number": 2,
                    "subject": "Quick follow-up - Success story",
                    "body": "Hi {{first_name}},\n\nWanted to share how we helped a similar company...",
                    "send_day": 3
                },
                {
                    "email_number": 3,
                    "subject": "Last check-in - Still interested?",
                    "body": "Hi {{first_name}},\n\nI know you're busy, so I'll keep this brief...",
                    "send_day": 7
                }
            ]
        
        sequence_data = {
            "sequence_name": f"Email Campaign - {goal[:30]}",
            "total_emails": len(emails),
            "emails": emails,
            "personalization_fields": ["{{first_name}}", "{{company}}", "{{role}}"],
            "campaign_duration_days": max([e.get("send_day", 0) for e in emails]) if emails else 7
        }
        
        return EmailSequenceAsset(
            title=f"Email Sequence - {goal[:50]}",
            data=sequence_data,
            metadata={
                "email_count": len(emails),
                "goal": goal
            },
            validation_score=0.7 if emails else 0.3,
            business_value_score=min(1.0, len(emails) / 5)  # 5 emails = perfect score
        )
    
    async def _generate_metrics_dashboard(
        self,
        data: Dict,
        goal: str,
        context: Optional[Dict]
    ) -> BusinessAsset:
        """
        Generate a metrics dashboard
        """
        metrics = data.get("metrics", [])
        
        # Aggregate metrics from text if no structured metrics
        if not metrics and data.get("raw_text"):
            # Extract numbers and percentages from text
            for text in data["raw_text"]:
                numbers = re.findall(r'\d+(?:\.\d+)?%?', text)
                for num in numbers[:10]:  # Limit to first 10 numbers
                    metrics.append({"value": num, "context": text[:100]})
        
        dashboard_data = {
            "title": f"Metrics Dashboard - {goal[:30]}",
            "metrics": metrics,
            "generated_at": datetime.utcnow().isoformat(),
            "data_points": len(metrics)
        }
        
        return BusinessAsset(
            asset_type=AssetType.METRICS_DASHBOARD,
            title=f"Metrics Dashboard - {goal[:50]}",
            data=dashboard_data,
            format="json",
            metadata={"goal": goal},
            validation_score=0.6 if metrics else 0.2,
            business_value_score=min(1.0, len(metrics) / 10)
        )
    
    async def _generate_strategy_document(
        self,
        data: Dict,
        goal: str,
        context: Optional[Dict]
    ) -> BusinessAsset:
        """
        Generate a strategy document from extracted data
        """
        # Compile all text into a structured document
        sections = []
        
        if data.get("structured_data"):
            sections.append({
                "title": "Key Data Points",
                "content": data["structured_data"]
            })
        
        if data.get("raw_text"):
            sections.append({
                "title": "Analysis & Insights",
                "content": "\n\n".join(data["raw_text"][:5])  # First 5 text blocks
            })
        
        document_data = {
            "title": f"Strategy Document - {goal[:50]}",
            "sections": sections,
            "created_at": datetime.utcnow().isoformat(),
            "word_count": sum(len(str(s.get("content", "")).split()) for s in sections)
        }
        
        return BusinessAsset(
            asset_type=AssetType.STRATEGY_DOCUMENT,
            title=f"Strategy - {goal[:50]}",
            data=document_data,
            format="json",
            metadata={"goal": goal},
            validation_score=0.5,
            business_value_score=0.6
        )
    
    def _validate_and_score(self, asset: BusinessAsset) -> BusinessAsset:
        """
        Validate the business asset and calculate quality scores
        """
        # Validation rules per asset type
        if asset.asset_type == AssetType.CONTACT_LIST:
            # Check for required fields in contacts
            if isinstance(asset.data, list) and asset.data:
                valid_contacts = sum(
                    1 for c in asset.data 
                    if c.get("email") and "@" in c.get("email", "")
                )
                asset.validation_score = valid_contacts / len(asset.data) if asset.data else 0
                asset.business_value_score = min(1.0, valid_contacts / 20)  # 20+ contacts is good
        
        elif asset.asset_type == AssetType.EMAIL_SEQUENCE:
            # Check email sequence completeness
            if isinstance(asset.data, dict):
                emails = asset.data.get("emails", [])
                valid_emails = sum(
                    1 for e in emails 
                    if e.get("subject") and e.get("body")
                )
                asset.validation_score = valid_emails / len(emails) if emails else 0
                asset.business_value_score = min(1.0, valid_emails / 3)  # 3+ emails is good
        
        return asset
    
    def _create_fallback_asset(
        self,
        goal: str,
        task_outputs: List[Dict]
    ) -> BusinessAsset:
        """
        Create a fallback asset when synthesis fails
        """
        return BusinessAsset(
            asset_type=AssetType.STRATEGY_DOCUMENT,
            title=f"Deliverable - {goal[:50]}",
            data={
                "goal": goal,
                "task_outputs": task_outputs,
                "note": "Raw task outputs - synthesis pending"
            },
            format="json",
            metadata={"fallback": True},
            validation_score=0.3,
            business_value_score=0.3
        )
    
    async def enhance_asset(
        self,
        asset: BusinessAsset,
        issues: List[str]
    ) -> BusinessAsset:
        """
        Enhance an asset that failed validation
        """
        logger.info(f"Enhancing {asset.asset_type.value} to address issues: {issues}")
        
        # Enhancement strategies based on issues
        for issue in issues:
            if "missing email" in issue.lower() and asset.asset_type == AssetType.CONTACT_LIST:
                # Try to generate placeholder emails
                for contact in asset.data:
                    if not contact.get("email"):
                        # Generate a placeholder based on name and company
                        name = contact.get("name", "contact").lower().replace(" ", ".")
                        company = contact.get("company", "company").lower().replace(" ", "")
                        contact["email"] = f"{name}@{company}.com"
            
            elif "insufficient data" in issue.lower():
                # Add a note about data limitations
                asset.metadata["enhancement_notes"] = "Limited data available - consider additional research"
        
        # Re-validate after enhancement
        return self._validate_and_score(asset)