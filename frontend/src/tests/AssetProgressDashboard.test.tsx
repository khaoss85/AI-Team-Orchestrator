/**
 * AssetProgressDashboard Test Suite
 * Comprehensive testing for the asset progress dashboard component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { act } from 'react-dom/test-utils';
import '@testing-library/jest-dom';

import { AssetProgressDashboard } from '../components/assets/AssetProgressDashboard';
import { mockWebSocket, setupWebSocketMock } from './mocks/websocket';

// Mock fetch for API calls
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock data
const mockGoalCompletionData = [
  {
    id: 'goal-1',
    metric_type: 'Customer Acquisition',
    target_value: 100,
    current_value: 75,
    progress_percentage: 75,
    asset_completion_rate: 80,
    quality_score: 0.85,
    status: 'active',
    requirements: [
      {
        id: 'req-1',
        asset_name: 'Customer Research Document',
        asset_type: 'document',
        priority: 'high',
        business_value_score: 0.9,
        progress_percentage: 100,
        artifacts: [
          {
            id: 'artifact-1',
            artifact_name: 'Customer Personas Analysis',
            artifact_type: 'document',
            status: 'approved',
            quality_score: 0.88,
            business_value_score: 0.9,
            created_at: '2024-01-01T10:00:00Z'
          }
        ]
      },
      {
        id: 'req-2',
        asset_name: 'Marketing Strategy',
        asset_type: 'document',
        priority: 'medium',
        business_value_score: 0.8,
        progress_percentage: 60,
        artifacts: [
          {
            id: 'artifact-2',
            artifact_name: 'Digital Marketing Plan',
            artifact_type: 'document',
            status: 'needs_improvement',
            quality_score: 0.65,
            business_value_score: 0.75,
            created_at: '2024-01-02T10:00:00Z'
          }
        ]
      }
    ]
  }
];

const mockQualityMetrics = {
  overall_quality_score: 0.82,
  artifacts_by_status: {
    approved: 15,
    needs_improvement: 8,
    requires_human_review: 3,
    in_progress: 5
  },
  quality_trends: [
    {
      date: '2024-01-01',
      quality_score: 0.78,
      artifacts_count: 20
    },
    {
      date: '2024-01-02',
      quality_score: 0.82,
      artifacts_count: 31
    }
  ],
  top_improvement_areas: [
    'Increase content specificity',
    'Add more data visualizations',
    'Improve actionability'
  ]
};

describe('AssetProgressDashboard', () => {
  setupWebSocketMock();

  beforeEach(() => {
    mockFetch.mockClear();
    
    // Setup successful API responses
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockGoalCompletionData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockQualityMetrics
      });
  });

  const renderDashboard = (workspaceId = 'test-workspace-123') => {
    return render(<AssetProgressDashboard workspaceId={workspaceId} />);
  };

  it('renders dashboard with loading state initially', () => {
    renderDashboard();
    
    expect(screen.getByText('Loading asset dashboard...')).toBeInTheDocument();
    expect(screen.getByRole('img')).toHaveClass('text-4xl text-blue-500');
  });

  it('displays goal completion data after loading', async () => {
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText('🎯 Asset-Driven Progress Dashboard')).toBeInTheDocument();
    });

    // Check goal completion metrics
    expect(screen.getByText('Customer Acquisition')).toBeInTheDocument();
    expect(screen.getByText('75 / 100')).toBeInTheDocument();
    expect(screen.getByText('75.0%')).toBeInTheDocument();
    
    // Check asset completion rate
    expect(screen.getByText('Asset Completion:')).toBeInTheDocument();
    expect(screen.getByText('80.0%')).toBeInTheDocument();
    
    // Check quality score
    expect(screen.getByText('Quality Score:')).toBeInTheDocument();
    expect(screen.getByText('0.85')).toBeInTheDocument();
  });

  it('displays key metrics cards correctly', async () => {
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText('Overall Quality Score')).toBeInTheDocument();
    });

    // Check quality score card
    expect(screen.getByText('0.8')).toBeInTheDocument(); // Overall quality

    // Check approved assets card
    expect(screen.getByText('Approved Assets')).toBeInTheDocument();
    expect(screen.getByText('15')).toBeInTheDocument();

    // Check active goals card
    expect(screen.getByText('Active Goals')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();

    // Check asset requirements card
    expect(screen.getByText('Asset Requirements')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
  });

  it('shows real-time connection status', async () => {
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText('Live Updates')).toBeInTheDocument();
    });

    const badge = screen.getByText('Live Updates').closest('.ant-badge');
    expect(badge).toBeInTheDocument();
  });

  it('handles real-time goal progress updates via WebSocket', async () => {
    renderDashboard();

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('Customer Acquisition')).toBeInTheDocument();
    });

    // Simulate WebSocket progress update
    act(() => {
      mockWebSocket.simulateGoalProgressUpdate({
        workspace_id: 'test-workspace-123',
        goal_id: 'goal-1',
        progress: 85,
        asset_completion_rate: 90,
        quality_score: 0.92
      });
    });

    await waitFor(() => {
      expect(screen.getByText('85.0%')).toBeInTheDocument();
      expect(screen.getByText('90.0%')).toBeInTheDocument();
      expect(screen.getByText('0.92')).toBeInTheDocument();
    });
  });

  it('handles real-time artifact quality updates', async () => {
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText('Customer Acquisition')).toBeInTheDocument();
    });

    // Simulate artifact quality update
    act(() => {
      mockWebSocket.simulateArtifactQualityUpdate({
        workspace_id: 'test-workspace-123',
        artifact_id: 'artifact-2',
        quality_score: 0.85,
        status: 'approved',
        validation_feedback: 'Quality improved after AI enhancement'
      });
    });

    // The component should update the artifact status
    await waitFor(() => {
      // This would depend on how the component handles the update
      expect(screen.getByText('approved')).toBeInTheDocument();
    });
  });

  it('handles new artifact creation notifications', async () => {
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText('Customer Acquisition')).toBeInTheDocument();
    });

    // Simulate new artifact creation
    act(() => {
      mockWebSocket.simulateNewArtifactCreated({
        workspace_id: 'test-workspace-123',
        artifact: {
          id: 'artifact-3',
          artifact_name: 'Competitive Analysis Report',
          artifact_type: 'document',
          status: 'draft',
          quality_score: 0.75
        }
      });
    });

    await waitFor(() => {
      expect(screen.getByText('Competitive Analysis Report')).toBeInTheDocument();
    });
  });

  it('displays quality performance trends chart', async () => {
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText('🛡️ Quality Performance Trends')).toBeInTheDocument();
    });

    // Check for chart container
    expect(screen.getByRole('img')).toBeInTheDocument(); // Recharts uses SVG
  });

  it('displays asset status distribution pie chart', async () => {
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText('📊 Asset Status Distribution')).toBeInTheDocument();
    });

    // The pie chart should show different status counts
    // (exact text depends on chart implementation)
  });

  it('displays asset pipeline visualization', async () => {
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText('🏗️ Asset Production Pipeline')).toBeInTheDocument();
    });
  });

  it('shows detailed asset requirements list', async () => {
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText('📋 Detailed Asset Requirements & Artifacts')).toBeInTheDocument();
    });

    // Check individual requirements
    expect(screen.getByText('Customer Research Document')).toBeInTheDocument();
    expect(screen.getByText('Marketing Strategy')).toBeInTheDocument();

    // Check artifacts under requirements
    expect(screen.getByText('Customer Personas Analysis')).toBeInTheDocument();
    expect(screen.getByText('Digital Marketing Plan')).toBeInTheDocument();

    // Check status badges
    expect(screen.getByText('approved')).toBeInTheDocument();
    expect(screen.getByText('needs improvement')).toBeInTheDocument();
  });

  it('displays AI quality recommendations when available', async () => {
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText('💡 AI Quality Recommendations')).toBeInTheDocument();
    });

    // Check recommendation items
    expect(screen.getByText('Increase content specificity')).toBeInTheDocument();
    expect(screen.getByText('Add more data visualizations')).toBeInTheDocument();
    expect(screen.getByText('Improve actionability')).toBeInTheDocument();
  });

  it('handles refresh data button click', async () => {
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText('Refresh Data')).toBeInTheDocument();
    });

    const refreshButton = screen.getByText('Refresh Data');
    
    // Clear previous fetch calls
    mockFetch.mockClear();
    
    // Setup new fetch responses
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockGoalCompletionData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockQualityMetrics
      });

    fireEvent.click(refreshButton);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(2);
    });
  });

  it('handles WebSocket connection errors gracefully', async () => {
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText('Customer Acquisition')).toBeInTheDocument();
    });

    // Simulate WebSocket error
    act(() => {
      mockWebSocket.simulateError('Connection failed');
    });

    await waitFor(() => {
      expect(screen.getByText('Disconnected')).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    // Setup failed API responses
    mockFetch
      .mockRejectedValueOnce(new Error('API Error'))
      .mockRejectedValueOnce(new Error('API Error'));

    renderDashboard();

    // Component should still render even with API errors
    await waitFor(() => {
      expect(screen.getByText('🎯 Asset-Driven Progress Dashboard')).toBeInTheDocument();
    });
  });

  it('handles ping/pong WebSocket messages', async () => {
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText('Customer Acquisition')).toBeInTheDocument();
    });

    // Simulate ping message
    act(() => {
      mockWebSocket.simulateMessage({
        type: 'ping',
        timestamp: new Date().toISOString()
      });
    });

    // Component should handle ping gracefully (no errors)
    expect(screen.getByText('Customer Acquisition')).toBeInTheDocument();
  });

  it('displays asset type statistics correctly', async () => {
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText('Customer Acquisition')).toBeInTheDocument();
    });

    // Check asset type breakdown
    const documentStats = screen.getAllByText('document');
    expect(documentStats).toHaveLength(4); // 2 requirements + 2 artifacts

    // Check type-specific metrics
    expect(screen.getByText('2')).toBeInTheDocument(); // Count in summary card
    expect(screen.getByText('Avg Quality: 0.77')).toBeInTheDocument(); // (0.88 + 0.65) / 2
  });

  it('supports goal subscription via WebSocket', async () => {
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText('Customer Acquisition')).toBeInTheDocument();
    });

    const lastInstance = mockWebSocket.getLastInstance();
    expect(lastInstance).toBeDefined();

    // Simulate subscribing to specific goal
    act(() => {
      lastInstance?.simulateMessage({
        type: 'subscribe_goal',
        goal_id: 'goal-1'
      });
    });

    // Component should handle subscription
    expect(screen.getByText('Customer Acquisition')).toBeInTheDocument();
  });

  it('maintains responsive design classes', async () => {
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText('🎯 Asset-Driven Progress Dashboard')).toBeInTheDocument();
    });

    // Check responsive grid classes
    const dashboard = screen.getByText('🎯 Asset-Driven Progress Dashboard').closest('.asset-progress-dashboard');
    expect(dashboard).toHaveClass('space-y-6');

    const keyMetrics = dashboard?.querySelector('.grid');
    expect(keyMetrics).toHaveClass('grid-cols-1', 'md:grid-cols-2', 'lg:grid-cols-4');
  });
});