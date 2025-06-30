import React, { useState, useEffect, useCallback } from 'react';
import { Card, Badge, Button, Table, Modal, Alert, Tooltip, Progress, Tag, Space } from 'antd';
import { 
  LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, 
  Tooltip as RechartsTooltip, ResponsiveContainer, BarChart, Bar, Cell 
} from 'recharts';
import {
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ClockCircleOutlined,
  EyeOutlined,
  EditOutlined,
  RobotOutlined,
  UserOutlined,
  AlertOutlined,
  ThunderboltOutlined,
  BulbOutlined
} from '@ant-design/icons';

interface QualityValidation {
  id: string;
  artifact_id: string;
  artifact_name: string;
  artifact_type: string;
  rule_name: string;
  score: number;
  passed: boolean;
  feedback: string;
  ai_assessment: string;
  improvement_suggestions: string[];
  validated_at: string;
  validation_model: string;
  business_impact: string;
  pillar_compliance_check: Record<string, any>;
}

interface AssetArtifact {
  id: string;
  artifact_name: string;
  artifact_type: string;
  status: 'draft' | 'approved' | 'needs_improvement' | 'requires_human_review';
  quality_score: number;
  business_value_score: number;
  actionability_score: number;
  ai_enhanced: boolean;
  validation_passed: boolean;
  created_at: string;
  validated_at?: string;
  content?: string;
}

interface QualityRule {
  id: string;
  asset_type: string;
  rule_name: string;
  threshold_score: number;
  auto_learning_enabled: boolean;
  performance_metrics: {
    pass_rate: number;
    avg_execution_time: number;
    total_validations: number;
  };
}

interface QualityDashboardData {
  overall_quality_score: number;
  quality_trends: Array<{
    timestamp: string;
    quality_score: number;
    validation_count: number;
    pass_rate: number;
  }>;
  validation_performance: Array<{
    rule_name: string;
    pass_rate: number;
    avg_score: number;
    execution_time: number;
  }>;
  pillar_compliance: Array<{
    pillar_name: string;
    compliance_rate: number;
    status: 'compliant' | 'warning' | 'non_compliant';
  }>;
  pending_reviews: AssetArtifact[];
  recent_validations: QualityValidation[];
}

interface QualityMonitoringPanelProps {
  workspaceId: string;
}

export const QualityMonitoringPanel: React.FC<QualityMonitoringPanelProps> = ({ workspaceId }) => {
  const [dashboardData, setDashboardData] = useState<QualityDashboardData | null>(null);
  const [selectedArtifact, setSelectedArtifact] = useState<AssetArtifact | null>(null);
  const [selectedValidation, setSelectedValidation] = useState<QualityValidation | null>(null);
  const [loading, setLoading] = useState(true);
  const [realTimeConnected, setRealTimeConnected] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Real-time quality updates via WebSocket (Pillar 10: Real-Time Thinking)
  useEffect(() => {
    let ws: WebSocket;
    
    const connectWebSocket = () => {
      try {
        ws = new WebSocket(`ws://localhost:8000/ws/quality/${workspaceId}`);
        
        ws.onopen = () => {
          console.log('🔗 Quality monitoring WebSocket connected');
          setRealTimeConnected(true);
        };
        
        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          handleRealTimeQualityUpdate(data);
        };
        
        ws.onclose = () => {
          console.log('🔌 Quality monitoring WebSocket disconnected');
          setRealTimeConnected(false);
          if (autoRefresh) {
            setTimeout(connectWebSocket, 3000);
          }
        };
        
        ws.onerror = (error) => {
          console.error('❌ Quality WebSocket error:', error);
          setRealTimeConnected(false);
        };
        
      } catch (error) {
        console.error('Failed to connect quality WebSocket:', error);
        setRealTimeConnected(false);
      }
    };
    
    if (autoRefresh) {
      connectWebSocket();
    }
    
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [workspaceId, autoRefresh]);

  // Handle real-time quality updates
  const handleRealTimeQualityUpdate = (data: any) => {
    switch (data.type) {
      case 'quality_validation_complete':
        addNewValidation(data.validation);
        break;
      case 'artifact_quality_updated':
        updateArtifactQuality(data.artifact_id, data.quality_score, data.status);
        break;
      case 'human_review_requested':
        addPendingReview(data.artifact);
        break;
      case 'ai_enhancement_complete':
        updateArtifactEnhancement(data.artifact_id, data.enhanced_content, data.new_score);
        break;
      default:
        console.log('Unknown quality update:', data.type);
    }
  };

  const addNewValidation = (validation: QualityValidation) => {
    setDashboardData(prev => {
      if (!prev) return prev;
      return {
        ...prev,
        recent_validations: [validation, ...prev.recent_validations.slice(0, 9)]
      };
    });
  };

  const updateArtifactQuality = (artifactId: string, qualityScore: number, status: string) => {
    setDashboardData(prev => {
      if (!prev) return prev;
      return {
        ...prev,
        pending_reviews: prev.pending_reviews.map(artifact =>
          artifact.id === artifactId
            ? { ...artifact, quality_score: qualityScore, status: status as any }
            : artifact
        )
      };
    });
  };

  const addPendingReview = (artifact: AssetArtifact) => {
    setDashboardData(prev => {
      if (!prev) return prev;
      return {
        ...prev,
        pending_reviews: [artifact, ...prev.pending_reviews]
      };
    });
  };

  const updateArtifactEnhancement = (artifactId: string, enhancedContent: string, newScore: number) => {
    setDashboardData(prev => {
      if (!prev) return prev;
      return {
        ...prev,
        pending_reviews: prev.pending_reviews.map(artifact =>
          artifact.id === artifactId
            ? { ...artifact, content: enhancedContent, quality_score: newScore, ai_enhanced: true }
            : artifact
        )
      };
    });
  };

  // Load quality dashboard data
  const loadQualityData = useCallback(async () => {
    try {
      setLoading(true);
      
      const response = await fetch(`/api/quality/${workspaceId}/dashboard`);
      const data = await response.json();
      setDashboardData(data);
      
    } catch (error) {
      console.error('Failed to load quality data:', error);
    } finally {
      setLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    loadQualityData();
  }, [loadQualityData]);

  // Auto-refresh every 30 seconds when not connected via WebSocket
  useEffect(() => {
    if (!realTimeConnected && autoRefresh) {
      const interval = setInterval(loadQualityData, 30000);
      return () => clearInterval(interval);
    }
  }, [realTimeConnected, autoRefresh, loadQualityData]);

  // Quality action handlers
  const handleApproveArtifact = async (artifactId: string) => {
    try {
      await fetch(`/api/quality/artifacts/${artifactId}/approve`, { method: 'POST' });
      await loadQualityData();
    } catch (error) {
      console.error('Failed to approve artifact:', error);
    }
  };

  const handleRequestEnhancement = async (artifactId: string) => {
    try {
      await fetch(`/api/quality/artifacts/${artifactId}/enhance`, { method: 'POST' });
      // Enhancement will be processed asynchronously, updates via WebSocket
    } catch (error) {
      console.error('Failed to request enhancement:', error);
    }
  };

  const handleHumanReview = async (artifactId: string, action: 'approve' | 'reject', feedback?: string) => {
    try {
      await fetch(`/api/quality/artifacts/${artifactId}/human-review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, feedback })
      });
      await loadQualityData();
    } catch (error) {
      console.error('Failed to submit human review:', error);
    }
  };

  if (loading || !dashboardData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <RobotOutlined className="text-4xl text-blue-500 mb-4" />
          <p>Loading quality monitoring dashboard...</p>
        </div>
      </div>
    );
  }

  // Prepare chart data
  const qualityTrendData = dashboardData.quality_trends.map(item => ({
    ...item,
    timestamp: new Date(item.timestamp).toLocaleTimeString(),
    pass_rate_percentage: item.pass_rate * 100
  }));

  const pillarComplianceData = dashboardData.pillar_compliance.map(item => ({
    ...item,
    compliance_percentage: item.compliance_rate * 100,
    color: item.status === 'compliant' ? '#52c41a' : 
           item.status === 'warning' ? '#faad14' : '#f5222d'
  }));

  // Table columns for validations
  const validationColumns = [
    {
      title: 'Artifact',
      dataIndex: 'artifact_name',
      key: 'artifact_name',
      render: (text: string, record: QualityValidation) => (
        <div>
          <div className="font-medium">{text}</div>
          <Tag color="blue">{record.artifact_type}</Tag>
        </div>
      )
    },
    {
      title: 'Rule',
      dataIndex: 'rule_name',
      key: 'rule_name'
    },
    {
      title: 'Score',
      dataIndex: 'score',
      key: 'score',
      render: (score: number) => (
        <Progress 
          percent={score * 100} 
          size="small" 
          status={score >= 0.8 ? 'success' : score >= 0.6 ? 'normal' : 'exception'}
          format={percent => `${(percent! / 100).toFixed(2)}`}
        />
      )
    },
    {
      title: 'Status',
      dataIndex: 'passed',
      key: 'passed',
      render: (passed: boolean) => (
        <Badge 
          color={passed ? 'green' : 'red'}
          text={passed ? 'Passed' : 'Failed'}
        />
      )
    },
    {
      title: 'Validated',
      dataIndex: 'validated_at',
      key: 'validated_at',
      render: (date: string) => new Date(date).toLocaleString()
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record: QualityValidation) => (
        <Space>
          <Button 
            size="small" 
            icon={<EyeOutlined />}
            onClick={() => setSelectedValidation(record)}
          >
            Details
          </Button>
        </Space>
      )
    }
  ];

  // Table columns for pending reviews
  const pendingReviewColumns = [
    {
      title: 'Artifact',
      dataIndex: 'artifact_name',
      key: 'artifact_name',
      render: (text: string, record: AssetArtifact) => (
        <div>
          <div className="font-medium">{text}</div>
          <Tag color="purple">{record.artifact_type}</Tag>
          {record.ai_enhanced && <Tag color="cyan" icon={<RobotOutlined />}>AI Enhanced</Tag>}
        </div>
      )
    },
    {
      title: 'Quality Score',
      dataIndex: 'quality_score',
      key: 'quality_score',
      render: (score: number) => (
        <div className="flex items-center space-x-2">
          <Progress 
            percent={score * 100} 
            size="small" 
            status={score >= 0.8 ? 'success' : score >= 0.6 ? 'normal' : 'exception'}
            format={percent => `${(percent! / 100).toFixed(2)}`}
          />
        </div>
      )
    },
    {
      title: 'Business Value',
      dataIndex: 'business_value_score',
      key: 'business_value_score',
      render: (score: number) => (
        <Badge 
          color={score >= 0.8 ? 'green' : score >= 0.6 ? 'blue' : 'orange'}
          text={score.toFixed(2)}
        />
      )
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusConfig = {
          requires_human_review: { color: 'red', icon: <UserOutlined /> },
          needs_improvement: { color: 'orange', icon: <EditOutlined /> },
          draft: { color: 'default', icon: <ClockCircleOutlined /> }
        };
        const config = statusConfig[status as keyof typeof statusConfig] || { color: 'default', icon: null };
        
        return (
          <Tag color={config.color} icon={config.icon}>
            {status.replace('_', ' ').toUpperCase()}
          </Tag>
        );
      }
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record: AssetArtifact) => (
        <Space>
          <Button 
            size="small" 
            icon={<EyeOutlined />}
            onClick={() => setSelectedArtifact(record)}
          >
            Review
          </Button>
          {record.status === 'needs_improvement' && (
            <Button 
              size="small" 
              type="primary" 
              ghost
              icon={<RobotOutlined />}
              onClick={() => handleRequestEnhancement(record.id)}
            >
              AI Enhance
            </Button>
          )}
          {record.status === 'requires_human_review' && (
            <>
              <Button 
                size="small" 
                type="primary" 
                icon={<CheckCircleOutlined />}
                onClick={() => handleApproveArtifact(record.id)}
              >
                Approve
              </Button>
            </>
          )}
        </Space>
      )
    }
  ];

  return (
    <div className="quality-monitoring-panel p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">🛡️ Quality Monitoring Dashboard</h1>
          <p className="text-gray-600">AI-driven quality assurance and human-in-the-loop validation</p>
        </div>
        <div className="flex items-center space-x-4">
          <Badge 
            color={realTimeConnected ? 'green' : 'red'} 
            text={realTimeConnected ? 'Live Quality Updates' : 'Offline'}
          />
          <Button 
            onClick={loadQualityData} 
            type="primary" 
            ghost
            icon={<ThunderboltOutlined />}
          >
            Refresh
          </Button>
        </div>
      </div>

      {/* Key Quality Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="text-center">
          <div className="space-y-2">
            <CheckCircleOutlined className="text-3xl text-green-500" />
            <div className="text-2xl font-bold">
              {dashboardData.overall_quality_score.toFixed(2)}
            </div>
            <div className="text-gray-600">Overall Quality</div>
          </div>
        </Card>

        <Card className="text-center">
          <div className="space-y-2">
            <UserOutlined className="text-3xl text-orange-500" />
            <div className="text-2xl font-bold">
              {dashboardData.pending_reviews.length}
            </div>
            <div className="text-gray-600">Pending Reviews</div>
          </div>
        </Card>

        <Card className="text-center">
          <div className="space-y-2">
            <RobotOutlined className="text-3xl text-blue-500" />
            <div className="text-2xl font-bold">
              {dashboardData.recent_validations.filter(v => v.passed).length}
            </div>
            <div className="text-gray-600">AI Validations Passed</div>
          </div>
        </Card>

        <Card className="text-center">
          <div className="space-y-2">
            <BulbOutlined className="text-3xl text-purple-500" />
            <div className="text-2xl font-bold">
              {dashboardData.pillar_compliance.filter(p => p.status === 'compliant').length}
            </div>
            <div className="text-gray-600">Pillars Compliant</div>
          </div>
        </Card>
      </div>

      {/* Quality Trends and Performance Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Quality Trends */}
        <Card title="📈 Quality Score Trends" className="h-80">
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={qualityTrendData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis domain={[0, 1]} />
              <RechartsTooltip 
                formatter={(value: number, name: string) => [
                  name === 'quality_score' ? value.toFixed(3) : value,
                  name === 'quality_score' ? 'Quality Score' : 
                  name === 'pass_rate_percentage' ? 'Pass Rate %' : name
                ]}
              />
              <Area 
                type="monotone" 
                dataKey="quality_score" 
                stroke="#1890ff" 
                fill="#1890ff" 
                fillOpacity={0.3}
              />
              <Line 
                type="monotone" 
                dataKey="pass_rate_percentage" 
                stroke="#52c41a" 
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </Card>

        {/* Pillar Compliance */}
        <Card title="🏛️ 14 Pillars Compliance" className="h-80">
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={pillarComplianceData} layout="horizontal">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" domain={[0, 100]} />
              <YAxis dataKey="pillar_name" type="category" width={100} />
              <RechartsTooltip formatter={(value: number) => [`${value.toFixed(1)}%`, 'Compliance']} />
              <Bar dataKey="compliance_percentage">
                {pillarComplianceData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>

      </div>

      {/* Quality Validation Performance */}
      <Card title="⚡ Validation Rule Performance">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left p-2">Rule Name</th>
                <th className="text-center p-2">Pass Rate</th>
                <th className="text-center p-2">Avg Score</th>
                <th className="text-center p-2">Execution Time</th>
                <th className="text-center p-2">Performance</th>
              </tr>
            </thead>
            <tbody>
              {dashboardData.validation_performance.map((rule, index) => (
                <tr key={index} className="border-b hover:bg-gray-50">
                  <td className="p-2 font-medium">{rule.rule_name}</td>
                  <td className="p-2 text-center">
                    <Badge 
                      color={rule.pass_rate >= 0.8 ? 'green' : rule.pass_rate >= 0.6 ? 'blue' : 'red'}
                      text={`${(rule.pass_rate * 100).toFixed(1)}%`}
                    />
                  </td>
                  <td className="p-2 text-center">{rule.avg_score.toFixed(2)}</td>
                  <td className="p-2 text-center">{rule.execution_time.toFixed(0)}ms</td>
                  <td className="p-2 text-center">
                    <div className="flex items-center justify-center">
                      {rule.pass_rate >= 0.8 && rule.execution_time < 2000 ? (
                        <CheckCircleOutlined className="text-green-500" />
                      ) : rule.pass_rate >= 0.6 || rule.execution_time < 5000 ? (
                        <ExclamationCircleOutlined className="text-yellow-500" />
                      ) : (
                        <AlertOutlined className="text-red-500" />
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Pending Human Reviews */}
      <Card title="👤 Pending Human Reviews" extra={
        <Badge count={dashboardData.pending_reviews.length} showZero />
      }>
        <Table 
          dataSource={dashboardData.pending_reviews}
          columns={pendingReviewColumns}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          scroll={{ x: 'max-content' }}
        />
      </Card>

      {/* Recent Quality Validations */}
      <Card title="🔍 Recent Quality Validations">
        <Table 
          dataSource={dashboardData.recent_validations}
          columns={validationColumns}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          scroll={{ x: 'max-content' }}
        />
      </Card>

      {/* Artifact Review Modal */}
      <Modal
        title={`📋 Review: ${selectedArtifact?.artifact_name}`}
        open={!!selectedArtifact}
        onCancel={() => setSelectedArtifact(null)}
        width={800}
        footer={selectedArtifact && [
          <Button key="cancel" onClick={() => setSelectedArtifact(null)}>
            Close
          </Button>,
          selectedArtifact.status === 'requires_human_review' && (
            <Button 
              key="approve" 
              type="primary"
              icon={<CheckCircleOutlined />}
              onClick={() => {
                handleHumanReview(selectedArtifact.id, 'approve');
                setSelectedArtifact(null);
              }}
            >
              Approve
            </Button>
          ),
          selectedArtifact.status === 'needs_improvement' && (
            <Button 
              key="enhance" 
              type="primary"
              icon={<RobotOutlined />}
              onClick={() => {
                handleRequestEnhancement(selectedArtifact.id);
                setSelectedArtifact(null);
              }}
            >
              AI Enhance
            </Button>
          )
        ]}
      >
        {selectedArtifact && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Type</label>
                <Tag color="blue">{selectedArtifact.artifact_type}</Tag>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Status</label>
                <Tag color="orange">{selectedArtifact.status.replace('_', ' ')}</Tag>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Quality Score</label>
                <Progress percent={selectedArtifact.quality_score * 100} size="small" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Business Value</label>
                <Progress percent={selectedArtifact.business_value_score * 100} size="small" />
              </div>
            </div>
            {selectedArtifact.content && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Content Preview</label>
                <div className="bg-gray-50 p-3 rounded border max-h-64 overflow-y-auto">
                  <pre className="whitespace-pre-wrap text-sm">
                    {selectedArtifact.content.substring(0, 1000)}
                    {selectedArtifact.content.length > 1000 && '...'}
                  </pre>
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* Validation Details Modal */}
      <Modal
        title={`🔍 Validation Details: ${selectedValidation?.rule_name}`}
        open={!!selectedValidation}
        onCancel={() => setSelectedValidation(null)}
        width={700}
        footer={[
          <Button key="close" onClick={() => setSelectedValidation(null)}>
            Close
          </Button>
        ]}
      >
        {selectedValidation && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Score</label>
                <Progress 
                  percent={selectedValidation.score * 100} 
                  status={selectedValidation.passed ? 'success' : 'exception'}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Model Used</label>
                <Tag>{selectedValidation.validation_model}</Tag>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">AI Assessment</label>
              <Alert 
                message={selectedValidation.ai_assessment}
                type={selectedValidation.passed ? 'success' : 'warning'}
                showIcon
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Feedback</label>
              <div className="bg-gray-50 p-3 rounded">
                {selectedValidation.feedback}
              </div>
            </div>
            
            {selectedValidation.improvement_suggestions.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Improvement Suggestions</label>
                <ul className="list-disc list-inside space-y-1">
                  {selectedValidation.improvement_suggestions.map((suggestion, index) => (
                    <li key={index} className="text-sm">{suggestion}</li>
                  ))}
                </ul>
              </div>
            )}
            
            {selectedValidation.business_impact && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Business Impact</label>
                <Alert 
                  message={selectedValidation.business_impact}
                  type="info"
                  showIcon
                />
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};