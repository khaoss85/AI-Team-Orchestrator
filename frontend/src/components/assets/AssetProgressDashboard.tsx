import React, { useState, useEffect } from 'react';
import { Card, Progress, Badge, Button, Tooltip } from 'antd';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, 
  ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line 
} from 'recharts';
import { 
  CheckCircleOutlined, 
  ClockCircleOutlined, 
  ExclamationCircleOutlined,
  RocketOutlined,
  TrophyOutlined,
  BulbOutlined
} from '@ant-design/icons';

interface AssetArtifact {
  id: string;
  artifact_name: string;
  artifact_type: string;
  status: 'draft' | 'approved' | 'needs_improvement' | 'requires_human_review';
  quality_score: number;
  business_value_score: number;
  created_at: string;
  validated_at?: string;
}

interface AssetRequirement {
  id: string;
  asset_name: string;
  asset_type: string;
  priority: 'high' | 'medium' | 'low';
  business_value_score: number;
  progress_percentage: number;
  artifacts: AssetArtifact[];
}

interface GoalCompletionData {
  id: string;
  metric_type: string;
  target_value: number;
  current_value: number;
  progress_percentage: number;
  status: string;
  asset_completion_rate: number;
  quality_score: number;
  requirements: AssetRequirement[];
}

interface QualityMetrics {
  overall_quality_score: number;
  artifacts_by_status: {
    approved: number;
    needs_improvement: number;
    requires_human_review: number;
    in_progress: number;
  };
  quality_trends: Array<{
    date: string;
    quality_score: number;
    artifacts_count: number;
  }>;
  top_improvement_areas: string[];
}

interface AssetProgressDashboardProps {
  workspaceId: string;
}

export const AssetProgressDashboard: React.FC<AssetProgressDashboardProps> = ({ workspaceId }) => {
  const [goalCompletion, setGoalCompletion] = useState<GoalCompletionData[]>([]);
  const [qualityMetrics, setQualityMetrics] = useState<QualityMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [realTimeConnected, setRealTimeConnected] = useState(false);

  // Real-time WebSocket connection (Pillar 10: Real-Time Thinking)
  useEffect(() => {
    let ws: WebSocket;
    
    const connectWebSocket = () => {
      try {
        ws = new WebSocket(`ws://localhost:8000/ws/assets/${workspaceId}`);
        
        ws.onopen = () => {
          console.log('🔗 Asset dashboard WebSocket connected');
          setRealTimeConnected(true);
        };
        
        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          handleRealTimeUpdate(data);
        };
        
        ws.onclose = () => {
          console.log('🔌 Asset dashboard WebSocket disconnected');
          setRealTimeConnected(false);
          // Retry connection after 3 seconds
          setTimeout(connectWebSocket, 3000);
        };
        
        ws.onerror = (error) => {
          console.error('❌ WebSocket error:', error);
          setRealTimeConnected(false);
        };
        
      } catch (error) {
        console.error('Failed to connect WebSocket:', error);
        setRealTimeConnected(false);
      }
    };
    
    connectWebSocket();
    
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [workspaceId]);

  // Handle real-time updates
  const handleRealTimeUpdate = (data: any) => {
    switch (data.type) {
      case 'goal_progress_update':
        updateGoalProgress(data.goal_id, data.progress, data.asset_completion_rate);
        break;
      case 'artifact_quality_update':
        updateArtifactQuality(data.artifact_id, data.quality_score, data.status);
        break;
      case 'new_artifact_created':
        addNewArtifact(data.artifact);
        break;
      default:
        console.log('Unknown real-time update:', data.type);
    }
  };

  const updateGoalProgress = (goalId: string, progress: number, assetCompletion: number) => {
    setGoalCompletion(prev => prev.map(goal => 
      goal.id === goalId 
        ? { ...goal, progress_percentage: progress, asset_completion_rate: assetCompletion }
        : goal
    ));
  };

  const updateArtifactQuality = (artifactId: string, qualityScore: number, status: string) => {
    setGoalCompletion(prev => prev.map(goal => ({
      ...goal,
      requirements: goal.requirements.map(req => ({
        ...req,
        artifacts: req.artifacts.map(artifact => 
          artifact.id === artifactId 
            ? { ...artifact, quality_score: qualityScore, status: status as any }
            : artifact
        )
      }))
    })));
  };

  const addNewArtifact = (newArtifact: AssetArtifact) => {
    // Add new artifact to appropriate requirement
    setGoalCompletion(prev => prev.map(goal => ({
      ...goal,
      requirements: goal.requirements.map(req => 
        req.id === newArtifact.id // This would need proper linking
          ? { ...req, artifacts: [...req.artifacts, newArtifact] }
          : req
      )
    })));
  };

  // Load initial data
  useEffect(() => {
    loadAssetData();
  }, [workspaceId]);

  const loadAssetData = async () => {
    try {
      setLoading(true);
      
      // Load goal completion data with asset breakdown
      const goalsResponse = await fetch(`/api/assets/goals/${workspaceId}/completion`);
      const goalsData = await goalsResponse.json();
      setGoalCompletion(goalsData);
      
      // Load quality metrics
      const qualityResponse = await fetch(`/api/assets/quality/${workspaceId}/metrics`);
      const qualityData = await qualityResponse.json();
      setQualityMetrics(qualityData);
      
    } catch (error) {
      console.error('Failed to load asset data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Color schemes for different statuses
  const statusColors = {
    approved: '#52c41a',
    needs_improvement: '#faad14', 
    requires_human_review: '#f5222d',
    in_progress: '#1890ff',
    draft: '#d9d9d9'
  };

  const assetTypeColors = {
    document: '#722ed1',
    data: '#13c2c2', 
    design: '#eb2f96',
    code: '#52c41a',
    presentation: '#fa8c16'
  };

  // Chart data preparation
  const qualityTrendData = qualityMetrics?.quality_trends?.map(item => ({
    ...item,
    date: new Date(item.date).toLocaleDateString()
  })) || [];

  const assetStatusData = qualityMetrics ? [
    { name: 'Approved', value: qualityMetrics.artifacts_by_status.approved, color: statusColors.approved },
    { name: 'Needs Improvement', value: qualityMetrics.artifacts_by_status.needs_improvement, color: statusColors.needs_improvement },
    { name: 'Human Review', value: qualityMetrics.artifacts_by_status.requires_human_review, color: statusColors.requires_human_review },
    { name: 'In Progress', value: qualityMetrics.artifacts_by_status.in_progress, color: statusColors.in_progress }
  ] : [];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <RocketOutlined className="text-4xl text-blue-500 mb-4" />
          <p>Loading asset dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="asset-progress-dashboard p-6 space-y-6">
      {/* Header with real-time status */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">🎯 Asset-Driven Progress Dashboard</h1>
          <p className="text-gray-600">Real-time tracking of concrete deliverables and quality metrics</p>
        </div>
        <div className="flex items-center space-x-4">
          <Badge 
            color={realTimeConnected ? 'green' : 'red'} 
            text={realTimeConnected ? 'Live Updates' : 'Disconnected'}
          />
          <Button onClick={loadAssetData} type="primary" ghost>
            Refresh Data
          </Button>
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="text-center">
          <div className="space-y-2">
            <TrophyOutlined className="text-3xl text-yellow-500" />
            <div className="text-2xl font-bold">
              {qualityMetrics?.overall_quality_score?.toFixed(1) || '0.0'}
            </div>
            <div className="text-gray-600">Overall Quality Score</div>
          </div>
        </Card>

        <Card className="text-center">
          <div className="space-y-2">
            <CheckCircleOutlined className="text-3xl text-green-500" />
            <div className="text-2xl font-bold">
              {qualityMetrics?.artifacts_by_status.approved || 0}
            </div>
            <div className="text-gray-600">Approved Assets</div>
          </div>
        </Card>

        <Card className="text-center">
          <div className="space-y-2">
            <ClockCircleOutlined className="text-3xl text-blue-500" />
            <div className="text-2xl font-bold">
              {goalCompletion.filter(g => g.status === 'active').length}
            </div>
            <div className="text-gray-600">Active Goals</div>
          </div>
        </Card>

        <Card className="text-center">
          <div className="space-y-2">
            <BulbOutlined className="text-3xl text-purple-500" />
            <div className="text-2xl font-bold">
              {goalCompletion.reduce((sum, g) => sum + g.requirements.length, 0)}
            </div>
            <div className="text-gray-600">Asset Requirements</div>
          </div>
        </Card>
      </div>

      {/* Main Dashboard Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Goal Completion with Asset Breakdown */}
        <Card title="🎯 Goal Completion & Asset Progress" className="h-96">
          <div className="space-y-4 max-h-80 overflow-y-auto">
            {goalCompletion.map(goal => (
              <GoalProgressCard 
                key={goal.id}
                goal={goal}
                showAssetBreakdown={true}
              />
            ))}
          </div>
        </Card>

        {/* Quality Performance Chart */}
        <Card title="🛡️ Quality Performance Trends" className="h-96">
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={qualityTrendData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis domain={[0, 1]} />
              <RechartsTooltip 
                formatter={(value: number) => [value.toFixed(2), 'Quality Score']}
              />
              <Line 
                type="monotone" 
                dataKey="quality_score" 
                stroke="#1890ff" 
                strokeWidth={2}
                dot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </Card>

        {/* Asset Status Distribution */}
        <Card title="📊 Asset Status Distribution" className="h-96">
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={assetStatusData}
                cx="50%"
                cy="50%"
                outerRadius={80}
                dataKey="value"
                label={({ name, value }) => `${name}: ${value}`}
              >
                {assetStatusData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <RechartsTooltip />
            </PieChart>
          </ResponsiveContainer>
        </Card>

        {/* Asset Pipeline Visualization */}
        <Card title="🏗️ Asset Production Pipeline" className="h-96">
          <AssetPipelineVisualization workspaceId={workspaceId} />
        </Card>

      </div>

      {/* Detailed Asset Requirements List */}
      <Card title="📋 Detailed Asset Requirements & Artifacts">
        <AssetRequirementsList 
          requirements={goalCompletion.flatMap(g => g.requirements)}
          onRefresh={loadAssetData}
        />
      </Card>

      {/* Quality Improvement Recommendations */}
      {qualityMetrics?.top_improvement_areas && qualityMetrics.top_improvement_areas.length > 0 && (
        <Card title="💡 AI Quality Recommendations" className="bg-blue-50">
          <div className="space-y-2">
            {qualityMetrics.top_improvement_areas.map((area, index) => (
              <div key={index} className="flex items-center space-x-2">
                <BulbOutlined className="text-blue-500" />
                <span>{area}</span>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};

// Goal Progress Card Component
const GoalProgressCard: React.FC<{ 
  goal: GoalCompletionData; 
  showAssetBreakdown: boolean;
}> = ({ goal, showAssetBreakdown }) => {
  const progressColor = goal.progress_percentage >= 80 ? 'success' : 
                       goal.progress_percentage >= 50 ? 'normal' : 'exception';

  return (
    <div className="border rounded-lg p-4 space-y-3">
      <div className="flex justify-between items-start">
        <div>
          <h4 className="font-semibold text-gray-800">{goal.metric_type}</h4>
          <p className="text-sm text-gray-600">
            {goal.current_value} / {goal.target_value}
          </p>
        </div>
        <Badge 
          color={progressColor === 'success' ? 'green' : progressColor === 'normal' ? 'blue' : 'red'}
          text={`${goal.progress_percentage.toFixed(1)}%`}
        />
      </div>

      <Progress 
        percent={goal.progress_percentage} 
        status={progressColor}
        size="small"
      />

      {showAssetBreakdown && (
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Asset Completion:</span>
            <span className="font-semibold">{goal.asset_completion_rate.toFixed(1)}%</span>
          </div>
          <div className="flex justify-between text-sm">
            <span>Quality Score:</span>
            <span className="font-semibold">{goal.quality_score.toFixed(2)}</span>
          </div>
          <div className="text-xs text-gray-500">
            {goal.requirements.length} requirements, {' '}
            {goal.requirements.flatMap(r => r.artifacts).length} artifacts
          </div>
        </div>
      )}
    </div>
  );
};

// Asset Pipeline Visualization Component
const AssetPipelineVisualization: React.FC<{ workspaceId: string }> = ({ workspaceId }) => {
  const [pipelineData, setPipelineData] = useState([
    { stage: 'Requirements', count: 12, color: '#722ed1' },
    { stage: 'In Progress', count: 8, color: '#1890ff' },
    { stage: 'Quality Review', count: 5, color: '#faad14' },
    { stage: 'Approved', count: 15, color: '#52c41a' }
  ]);

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={pipelineData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="stage" />
          <YAxis />
          <RechartsTooltip />
          <Bar dataKey="count" fill="#1890ff">
            {pipelineData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

// Asset Requirements List Component
const AssetRequirementsList: React.FC<{ 
  requirements: AssetRequirement[];
  onRefresh: () => void;
}> = ({ requirements, onRefresh }) => {
  return (
    <div className="space-y-4">
      {requirements.map(requirement => (
        <div key={requirement.id} className="border rounded-lg p-4">
          <div className="flex justify-between items-start mb-3">
            <div>
              <h4 className="font-semibold">{requirement.asset_name}</h4>
              <div className="flex items-center space-x-4 text-sm text-gray-600">
                <Badge color={assetTypeColors[requirement.asset_type as keyof typeof assetTypeColors]} text={requirement.asset_type} />
                <span>Priority: {requirement.priority}</span>
                <span>Business Value: {requirement.business_value_score.toFixed(2)}</span>
              </div>
            </div>
            <Progress 
              type="circle" 
              percent={requirement.progress_percentage} 
              width={60}
              format={percent => `${percent}%`}
            />
          </div>

          {requirement.artifacts.length > 0 && (
            <div className="space-y-2">
              <h5 className="font-medium text-gray-700">Artifacts ({requirement.artifacts.length}):</h5>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                {requirement.artifacts.map(artifact => (
                  <div key={artifact.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <div>
                      <div className="font-medium text-sm">{artifact.artifact_name}</div>
                      <div className="text-xs text-gray-500">Quality: {artifact.quality_score.toFixed(2)}</div>
                    </div>
                    <Badge 
                      color={statusColors[artifact.status as keyof typeof statusColors]}
                      text={artifact.status.replace('_', ' ')}
                    />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

const statusColors = {
  approved: 'green',
  needs_improvement: 'orange', 
  requires_human_review: 'red',
  in_progress: 'blue',
  draft: 'default'
};

const assetTypeColors = {
  document: '#722ed1',
  data: '#13c2c2', 
  design: '#eb2f96',
  code: '#52c41a',
  presentation: '#fa8c16'
};