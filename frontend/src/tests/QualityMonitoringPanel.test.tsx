/**
 * QualityMonitoringPanel Test Suite
 * Comprehensive testing for the quality monitoring and validation interface
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { act } from 'react-dom/test-utils';
import '@testing-library/jest-dom';

import { QualityMonitoringPanel } from '../components/quality/QualityMonitoringPanel';
import { mockWebSocket, setupWebSocketMock } from './mocks/websocket';

// Mock fetch for API calls
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock data
const mockQualityDashboardData = {
  overall_quality_score: 0.84,
  quality_trends: [
    {
      timestamp: '2024-01-01T10:00:00Z',
      quality_score: 0.78,
      validation_count: 25,
      pass_rate: 0.76
    },
    {
      timestamp: '2024-01-01T11:00:00Z',
      quality_score: 0.84,
      validation_count: 30,
      pass_rate: 0.80
    }
  ],
  validation_performance: [
    {
      rule_name: 'Content Completeness Check',
      pass_rate: 0.85,
      avg_score: 0.82,
      execution_time: 1200
    },
    {
      rule_name: 'Business Value Assessment',
      pass_rate: 0.78,
      avg_score: 0.75,
      execution_time: 1800
    },
    {
      rule_name: 'Actionability Validation',
      pass_rate: 0.92,
      avg_score: 0.88,
      execution_time: 950
    }
  ],
  pillar_compliance: [
    {
      pillar_name: 'Concrete Deliverables',
      compliance_rate: 0.95,
      status: 'compliant'
    },
    {
      pillar_name: 'AI-Driven',
      compliance_rate: 0.88,
      status: 'compliant'
    },
    {
      pillar_name: 'Quality Gates',
      compliance_rate: 0.72,
      status: 'warning'
    }
  ],
  pending_reviews: [
    {
      id: 'artifact-1',
      artifact_name: 'Customer Research Analysis',
      artifact_type: 'document',
      status: 'requires_human_review',
      quality_score: 0.73,
      business_value_score: 0.85,
      actionability_score: 0.68,
      ai_enhanced: false,
      validation_passed: false,
      created_at: '2024-01-01T10:00:00Z'
    },
    {
      id: 'artifact-2',
      artifact_name: 'Marketing Strategy Document',
      artifact_type: 'document',
      status: 'needs_improvement',
      quality_score: 0.61,
      business_value_score: 0.70,
      actionability_score: 0.55,
      ai_enhanced: true,
      validation_passed: false,
      created_at: '2024-01-01T09:30:00Z'
    }
  ],
  recent_validations: [
    {
      id: 'validation-1',
      artifact_id: 'artifact-1',
      artifact_name: 'Customer Research Analysis',
      artifact_type: 'document',
      rule_name: 'Content Completeness Check',
      score: 0.73,
      passed: false,
      feedback: 'Document lacks specific data points and actionable recommendations',
      ai_assessment: 'Content is well-structured but needs more concrete examples',
      improvement_suggestions: [
        'Add specific customer data points',
        'Include actionable recommendations',
        'Provide clear next steps'
      ],
      validated_at: '2024-01-01T10:15:00Z',
      validation_model: 'gpt-4o-mini',
      business_impact: 'Medium impact - requires enhancement for stakeholder use',
      pillar_compliance_check: {
        concrete_deliverables: false,
        actionability: false,
        business_value: true
      }
    }
  ]
};

describe('QualityMonitoringPanel', () => {
  setupWebSocketMock();

  beforeEach(() => {
    mockFetch.mockClear();
    
    // Setup successful API response
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockQualityDashboardData
    });
  });

  const renderPanel = (workspaceId = 'test-workspace-123') => {
    return render(<QualityMonitoringPanel workspaceId={workspaceId} />);
  };

  it('renders loading state initially', () => {
    renderPanel();
    
    expect(screen.getByText('Loading quality monitoring dashboard...')).toBeInTheDocument();
    expect(screen.getByRole('img')).toHaveClass('text-4xl text-blue-500');
  });

  it('displays quality monitoring header and controls', async () => {
    renderPanel();

    await waitFor(() => {
      expect(screen.getByText('🛡️ Quality Monitoring Dashboard')).toBeInTheDocument();
    });

    expect(screen.getByText('AI-driven quality assurance and human-in-the-loop validation')).toBeInTheDocument();
    expect(screen.getByText('Live Quality Updates')).toBeInTheDocument();
    expect(screen.getByText('Refresh')).toBeInTheDocument();
  });

  it('displays key quality metrics cards', async () => {
    renderPanel();

    await waitFor(() => {
      expect(screen.getByText('Overall Quality')).toBeInTheDocument();
    });

    // Check overall quality score
    expect(screen.getByText('0.84')).toBeInTheDocument();

    // Check pending reviews count
    expect(screen.getByText('Pending Reviews')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();

    // Check AI validations passed
    expect(screen.getByText('AI Validations Passed')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument(); // 1 recent validation that passed

    // Check pillars compliant
    expect(screen.getByText('Pillars Compliant')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument(); // 2 compliant pillars
  });

  it('displays quality trends chart', async () => {
    renderPanel();

    await waitFor(() => {
      expect(screen.getByText('📈 Quality Score Trends')).toBeInTheDocument();
    });

    // Chart should be rendered (Recharts uses SVG)
    expect(document.querySelector('svg')).toBeInTheDocument();
  });

  it('displays pillar compliance chart', async () => {
    renderPanel();

    await waitFor(() => {
      expect(screen.getByText('🏛️ 14 Pillars Compliance')).toBeInTheDocument();
    });

    // Check individual pillars
    expect(screen.getByText('Concrete Deliverables')).toBeInTheDocument();
    expect(screen.getByText('AI-Driven')).toBeInTheDocument();
    expect(screen.getByText('Quality Gates')).toBeInTheDocument();
  });

  it('displays validation rule performance table', async () => {
    renderPanel();

    await waitFor(() => {
      expect(screen.getByText('⚡ Validation Rule Performance')).toBeInTheDocument();
    });

    // Check rule names
    expect(screen.getByText('Content Completeness Check')).toBeInTheDocument();
    expect(screen.getByText('Business Value Assessment')).toBeInTheDocument();
    expect(screen.getByText('Actionability Validation')).toBeInTheDocument();

    // Check pass rates
    expect(screen.getByText('85.0%')).toBeInTheDocument();
    expect(screen.getByText('78.0%')).toBeInTheDocument();
    expect(screen.getByText('92.0%')).toBeInTheDocument();

    // Check execution times
    expect(screen.getByText('1200ms')).toBeInTheDocument();
    expect(screen.getByText('1800ms')).toBeInTheDocument();
    expect(screen.getByText('950ms')).toBeInTheDocument();
  });

  it('displays pending human reviews table', async () => {
    renderPanel();

    await waitFor(() => {
      expect(screen.getByText('👤 Pending Human Reviews')).toBeInTheDocument();
    });

    // Check artifact names
    expect(screen.getByText('Customer Research Analysis')).toBeInTheDocument();
    expect(screen.getByText('Marketing Strategy Document')).toBeInTheDocument();

    // Check status tags
    expect(screen.getByText('REQUIRES HUMAN REVIEW')).toBeInTheDocument();
    expect(screen.getByText('NEEDS IMPROVEMENT')).toBeInTheDocument();

    // Check AI enhanced indicators
    const aiTags = screen.getAllByText('AI Enhanced');
    expect(aiTags).toHaveLength(1); // Only one artifact is AI enhanced
  });

  it('displays recent quality validations table', async () => {
    renderPanel();

    await waitFor(() => {
      expect(screen.getByText('🔍 Recent Quality Validations')).toBeInTheDocument();
    });

    // Check validation details
    expect(screen.getByText('Content Completeness Check')).toBeInTheDocument();
    expect(screen.getByText('Failed')).toBeInTheDocument();
  });

  it('handles approve artifact action', async () => {
    // Mock approve API call
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockQualityDashboardData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: 'Artifact approved successfully' })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockQualityDashboardData // Refresh data
      });

    renderPanel();

    await waitFor(() => {
      expect(screen.getByText('Customer Research Analysis')).toBeInTheDocument();
    });

    const approveButton = screen.getByText('Approve');
    fireEvent.click(approveButton);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/quality/artifacts/artifact-1/approve',
        { method: 'POST' }
      );
    });
  });

  it('handles AI enhance artifact action', async () => {
    // Mock enhance API call
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockQualityDashboardData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: 'AI enhancement started' })
      });

    renderPanel();

    await waitFor(() => {
      expect(screen.getByText('Marketing Strategy Document')).toBeInTheDocument();
    });

    const enhanceButton = screen.getByText('AI Enhance');
    fireEvent.click(enhanceButton);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/quality/artifacts/artifact-2/enhance',
        { method: 'POST' }
      );
    });
  });

  it('opens artifact review modal', async () => {
    renderPanel();

    await waitFor(() => {
      expect(screen.getByText('Customer Research Analysis')).toBeInTheDocument();
    });

    const reviewButton = screen.getByText('Review');
    fireEvent.click(reviewButton);

    await waitFor(() => {
      expect(screen.getByText('📋 Review: Customer Research Analysis')).toBeInTheDocument();
    });

    // Check modal content
    expect(screen.getByText('Type')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
    expect(screen.getByText('Quality Score')).toBeInTheDocument();
    expect(screen.getByText('Business Value')).toBeInTheDocument();
  });

  it('opens validation details modal', async () => {
    renderPanel();

    await waitFor(() => {
      expect(screen.getByText('Content Completeness Check')).toBeInTheDocument();
    });

    const detailsButton = screen.getByText('Details');
    fireEvent.click(detailsButton);

    await waitFor(() => {
      expect(screen.getByText('🔍 Validation Details: Content Completeness Check')).toBeInTheDocument();
    });

    // Check validation details
    expect(screen.getByText('AI Assessment')).toBeInTheDocument();
    expect(screen.getByText('Feedback')).toBeInTheDocument();
    expect(screen.getByText('Improvement Suggestions')).toBeInTheDocument();
  });

  it('handles real-time quality validation updates', async () => {
    renderPanel();

    await waitFor(() => {
      expect(screen.getByText('Customer Research Analysis')).toBeInTheDocument();
    });

    // Simulate real-time quality validation complete
    act(() => {
      mockWebSocket.simulateQualityValidationComplete({
        workspace_id: 'test-workspace-123',
        validation: {
          id: 'validation-2',
          artifact_id: 'artifact-1',
          score: 0.88,
          passed: true,
          feedback: 'Quality validation passed after improvements'
        }
      });
    });

    await waitFor(() => {
      // New validation should appear in recent validations
      expect(screen.getByText('Quality validation passed after improvements')).toBeInTheDocument();
    });
  });

  it('handles real-time artifact quality updates', async () => {
    renderPanel();

    await waitFor(() => {
      expect(screen.getByText('Customer Research Analysis')).toBeInTheDocument();
    });

    // Simulate artifact quality update
    act(() => {
      mockWebSocket.simulateArtifactQualityUpdate({
        workspace_id: 'test-workspace-123',
        artifact_id: 'artifact-1',
        quality_score: 0.88,
        status: 'approved',
        validation_feedback: 'Quality improved significantly'
      });
    });

    await waitFor(() => {
      // Artifact status should be updated
      expect(screen.getByText('0.88')).toBeInTheDocument();
    });
  });

  it('handles real-time human review requests', async () => {
    renderPanel();

    await waitFor(() => {
      expect(screen.getByText('Customer Research Analysis')).toBeInTheDocument();
    });

    // Simulate new human review request
    act(() => {
      mockWebSocket.simulateHumanReviewRequested({
        workspace_id: 'test-workspace-123',
        artifact: {
          id: 'artifact-3',
          artifact_name: 'New Product Specification',
          artifact_type: 'document',
          quality_score: 0.65,
          status: 'requires_human_review'
        },
        review_reason: 'Quality score below threshold'
      });
    });

    await waitFor(() => {
      expect(screen.getByText('New Product Specification')).toBeInTheDocument();
    });
  });

  it('handles real-time AI enhancement completion', async () => {
    renderPanel();

    await waitFor(() => {
      expect(screen.getByText('Marketing Strategy Document')).toBeInTheDocument();
    });

    // Simulate AI enhancement completion
    act(() => {
      mockWebSocket.simulateAIEnhancementComplete({
        workspace_id: 'test-workspace-123',
        artifact_id: 'artifact-2',
        enhanced_content: 'Enhanced content with improved quality...',
        new_quality_score: 0.85
      });
    });

    await waitFor(() => {
      expect(screen.getByText('0.85')).toBeInTheDocument();
    });
  });

  it('handles WebSocket connection status changes', async () => {
    renderPanel();

    await waitFor(() => {
      expect(screen.getByText('Live Quality Updates')).toBeInTheDocument();
    });

    // Simulate WebSocket disconnection
    act(() => {
      mockWebSocket.simulateClose(1000, 'Connection closed');
    });

    await waitFor(() => {
      expect(screen.getByText('Offline')).toBeInTheDocument();
    });
  });

  it('handles ping/pong WebSocket messages', async () => {
    renderPanel();

    await waitFor(() => {
      expect(screen.getByText('Customer Research Analysis')).toBeInTheDocument();
    });

    // Simulate ping message
    act(() => {
      mockWebSocket.simulateMessage({
        type: 'ping',
        timestamp: new Date().toISOString()
      });
    });

    // Component should handle ping gracefully
    expect(screen.getByText('Customer Research Analysis')).toBeInTheDocument();
  });

  it('handles refresh button click', async () => {
    renderPanel();

    await waitFor(() => {
      expect(screen.getByText('Refresh')).toBeInTheDocument();
    });

    const refreshButton = screen.getByText('Refresh');
    
    // Clear previous fetch calls
    mockFetch.mockClear();
    
    // Setup new fetch response
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockQualityDashboardData
    });

    fireEvent.click(refreshButton);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/quality/test-workspace-123/dashboard');
    });
  });

  it('handles API errors gracefully', async () => {
    // Setup failed API response
    mockFetch.mockRejectedValueOnce(new Error('API Error'));

    renderPanel();

    // Component should still render header even with API errors
    await waitFor(() => {
      expect(screen.getByText('🛡️ Quality Monitoring Dashboard')).toBeInTheDocument();
    });
  });

  it('displays performance indicators correctly', async () => {
    renderPanel();

    await waitFor(() => {
      expect(screen.getByText('⚡ Validation Rule Performance')).toBeInTheDocument();
    });

    // Check performance icons
    const healthyIcons = screen.getAllByTestId('check-circle');
    const warningIcons = screen.getAllByTestId('exclamation-circle');
    const criticalIcons = screen.getAllByTestId('alert');

    // Should have different performance indicators based on rule performance
    expect(healthyIcons.length + warningIcons.length + criticalIcons.length).toBeGreaterThan(0);
  });

  it('maintains responsive design classes', async () => {
    renderPanel();

    await waitFor(() => {
      expect(screen.getByText('🛡️ Quality Monitoring Dashboard')).toBeInTheDocument();
    });

    // Check responsive grid classes
    const panel = screen.getByText('🛡️ Quality Monitoring Dashboard').closest('.quality-monitoring-panel');
    expect(panel).toHaveClass('space-y-6');

    const keyMetrics = panel?.querySelector('.grid');
    expect(keyMetrics).toHaveClass('grid-cols-1', 'md:grid-cols-4');
  });
});