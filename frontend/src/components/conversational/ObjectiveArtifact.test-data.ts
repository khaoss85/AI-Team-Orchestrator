// Test data for enhanced ObjectiveArtifact component
// This file demonstrates the expected data format for the enhanced component

export const mockDeliverableWithDisplayContent = {
  id: "test-deliverable-1",
  title: "Enhanced Email Template",
  created_at: "2025-08-28T12:00:00Z",
  status: "completed",
  type: "email_template",
  
  // NEW: Enhanced display content (AI-generated HTML)
  display_content: `
    <div class="email-template">
      <h3>📧 Business Solutions Email Template</h3>
      <div class="email-header">
        <p><strong>Subject:</strong> Let's Elevate Your Business to New Heights</p>
        <p><strong>From:</strong> Your Business Partner</p>
      </div>
      <div class="email-body">
        <p>Hello [Recipient's First Name],</p>
        <p>I hope this message finds you well. I wanted to reach out because I believe we have an incredible opportunity to transform your business operations.</p>
        
        <h4>🎯 What We Offer:</h4>
        <ul>
          <li><strong>Strategic Consulting</strong> - Tailored growth strategies</li>
          <li><strong>Technology Integration</strong> - Modern solutions for efficiency</li>
          <li><strong>Market Analysis</strong> - Data-driven insights</li>
        </ul>
        
        <div class="call-to-action" style="background: #f0f9ff; padding: 16px; border-radius: 8px; margin: 16px 0;">
          <p><strong>Ready to get started?</strong> Let's schedule a 15-minute discovery call to discuss your specific needs.</p>
          <p>📅 <a href="#book-call">Book Your Free Consultation</a></p>
        </div>
        
        <p>Looking forward to partnering with you,<br>
        [Your Name]</p>
      </div>
    </div>
  `,
  display_format: "html",
  display_summary: "Professional email template for business outreach with clear call-to-action and structured content",
  display_quality_score: 92,
  user_friendliness_score: 88,
  content_transformation_status: "success",
  
  // Legacy content (JSON format - should be deprioritized)
  content: {
    subject: "Let's Elevate Your Business to New Heights",
    body: "Hello [Recipient's First Name]...",
    metadata: {
      template_type: "business_outreach",
      estimated_read_time: "45 seconds"
    }
  }
}

export const mockDeliverableLegacyOnly = {
  id: "test-deliverable-2", 
  title: "Legacy Content Deliverable",
  created_at: "2025-08-28T11:00:00Z",
  status: "completed",
  type: "social_media_post",
  
  // Only legacy content - should show with deprecation warning
  content: {
    platform: "LinkedIn",
    post: "🚀 Exciting news! We're launching our new AI-powered business solutions...",
    hashtags: ["#AI", "#Business", "#Innovation"],
    estimated_engagement: "500+ interactions"
  }
}

export const mockDeliverableWithError = {
  id: "test-deliverable-3",
  title: "Failed Transformation",
  created_at: "2025-08-28T10:00:00Z", 
  status: "completed",
  type: "marketing_copy",
  
  // Transformation failed - should show error state
  content: {
    headline: "Revolutionary Product Launch",
    body: "Experience the future with our cutting-edge solution..."
  },
  content_transformation_status: "failed",
  transformation_error: "HTML generation failed due to content complexity",
  can_retry_transformation: true,
  available_formats: ["html", "markdown", "text"]
}

export const mockObjectiveData = {
  objective: {
    id: "goal-123",
    description: "Create comprehensive marketing materials for product launch",
    targetDate: "2025-09-15T00:00:00Z",
    progress: 75
  },
  progress: 75,
  deliverables: [
    mockDeliverableWithDisplayContent,
    mockDeliverableLegacyOnly,
    mockDeliverableWithError
  ],
  current_value: 3,
  target_value: 4,
  status: "active",
  priority: "high",
  created_at: "2025-08-20T00:00:00Z",
  updated_at: "2025-08-28T12:00:00Z"
}

// Usage example:
// <ObjectiveArtifact 
//   objectiveData={mockObjectiveData}
//   workspaceId="workspace-123"
//   title="Marketing Materials"
// />