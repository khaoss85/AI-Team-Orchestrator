import React, { useState, useEffect, useCallback } from 'react';
import { 
  Table, Card, Button, Modal, Tag, Badge, Progress, Tooltip, 
  Input, Select, Space, Alert, Descriptions, Typography, Divider 
} from 'antd';
import { 
  EyeOutlined, EditOutlined, DownloadOutlined, ShareAltOutlined,
  CheckCircleOutlined, ExclamationCircleOutlined, ClockCircleOutlined,
  RobotOutlined, FileTextOutlined, DatabaseOutlined, DesignOutlined,
  CodeOutlined, PresentationOutlined, SearchOutlined, FilterOutlined,
  BulbOutlined, ThunderboltOutlined, UserOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';

const { Search } = Input;
const { Option } = Select;
const { Text, Paragraph } = Typography;

interface AssetArtifact {
  id: string;
  requirement_id: string;
  artifact_name: string;
  artifact_type: 'document' | 'data' | 'design' | 'code' | 'presentation';
  artifact_format: string;
  content: string;
  status: 'draft' | 'approved' | 'needs_improvement' | 'requires_human_review';
  quality_score: number;
  business_value_score: number;
  actionability_score: number;
  ai_enhanced: boolean;
  validation_passed: boolean;
  created_at: string;
  updated_at: string;
  validated_at?: string;
  metadata: Record<string, any>;
  tags: string[];
  pillar_compliance: Record<string, any>;
  openai_file_id?: string;
}

interface AssetRequirement {
  id: string;
  goal_id: string;
  asset_name: string;
  asset_type: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
  business_value_score: number;
  progress_percentage: number;
}

interface QualityValidation {
  id: string;
  artifact_id: string;
  score: number;
  passed: boolean;
  feedback: string;
  improvement_suggestions: string[];
  validated_at: string;
}

interface AssetArtifactsListProps {
  workspaceId: string;
  enableQualityActions?: boolean;
  enableAIEnhancement?: boolean;
  onArtifactUpdate?: (artifact: AssetArtifact) => void;
}

export const AssetArtifactsList: React.FC<AssetArtifactsListProps> = ({
  workspaceId,
  enableQualityActions = true,
  enableAIEnhancement = true,
  onArtifactUpdate
}) => {
  const [artifacts, setArtifacts] = useState<AssetArtifact[]>([]);
  const [requirements, setRequirements] = useState<AssetRequirement[]>([]);
  const [validations, setValidations] = useState<QualityValidation[]>([]);
  const [selectedArtifact, setSelectedArtifact] = useState<AssetArtifact | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchText, setSearchText] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [showEnhancementModal, setShowEnhancementModal] = useState(false);

  // Asset type configurations
  const assetTypeConfig = {
    document: { 
      icon: <FileTextOutlined />, 
      color: '#722ed1',
      description: 'Reports, strategies, analyses, plans, guides'
    },
    data: { 
      icon: <DatabaseOutlined />, 
      color: '#13c2c2',
      description: 'Databases, lists, datasets, spreadsheets'
    },
    design: { 
      icon: <DesignOutlined />, 
      color: '#eb2f96',
      description: 'Mockups, graphics, layouts, wireframes'
    },
    code: { 
      icon: <CodeOutlined />, 
      color: '#52c41a',
      description: 'Scripts, applications, tools, automations'
    },
    presentation: { 
      icon: <PresentationOutlined />, 
      color: '#fa8c16',
      description: 'Slides, demos, training materials'
    }
  };

  const statusConfig = {
    draft: { color: 'default', icon: <ClockCircleOutlined /> },
    approved: { color: 'success', icon: <CheckCircleOutlined /> },
    needs_improvement: { color: 'warning', icon: <ExclamationCircleOutlined /> },
    requires_human_review: { color: 'error', icon: <UserOutlined /> }
  };

  // Load artifacts and related data
  const loadArtifacts = useCallback(async () => {
    try {
      setLoading(true);
      
      // Load artifacts
      const artifactsResponse = await fetch(`/api/assets/artifacts/${workspaceId}`);
      const artifactsData = await artifactsResponse.json();
      setArtifacts(artifactsData);
      
      // Load requirements
      const requirementsResponse = await fetch(`/api/assets/requirements/${workspaceId}`);
      const requirementsData = await requirementsResponse.json();
      setRequirements(requirementsData);
      
      // Load validations
      const validationsResponse = await fetch(`/api/quality/validations/${workspaceId}`);
      const validationsData = await validationsResponse.json();
      setValidations(validationsData);
      
    } catch (error) {
      console.error('Failed to load artifacts:', error);
    } finally {
      setLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    loadArtifacts();
  }, [loadArtifacts]);

  // Filter artifacts based on search and filters
  const filteredArtifacts = artifacts.filter(artifact => {
    const matchesSearch = searchText === '' || 
      artifact.artifact_name.toLowerCase().includes(searchText.toLowerCase()) ||
      artifact.content.toLowerCase().includes(searchText.toLowerCase()) ||
      artifact.tags.some(tag => tag.toLowerCase().includes(searchText.toLowerCase()));
    
    const matchesStatus = statusFilter === 'all' || artifact.status === statusFilter;
    const matchesType = typeFilter === 'all' || artifact.artifact_type === typeFilter;
    
    return matchesSearch && matchesStatus && matchesType;
  });

  // Quality action handlers
  const handleApproveArtifact = async (artifactId: string) => {
    try {
      await fetch(`/api/quality/artifacts/${artifactId}/approve`, { method: 'POST' });
      await loadArtifacts();
      onArtifactUpdate && onArtifactUpdate(artifacts.find(a => a.id === artifactId)!);
    } catch (error) {
      console.error('Failed to approve artifact:', error);
    }
  };

  const handleRequestEnhancement = async (artifactId: string) => {
    try {
      await fetch(`/api/quality/artifacts/${artifactId}/enhance`, { method: 'POST' });
      // Enhancement will be processed asynchronously
    } catch (error) {
      console.error('Failed to request enhancement:', error);
    }
  };

  const handleDownloadArtifact = async (artifact: AssetArtifact) => {
    try {
      const blob = new Blob([artifact.content], { type: 'text/plain' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${artifact.artifact_name}.${artifact.artifact_format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to download artifact:', error);
    }
  };

  // Get requirement name for artifact
  const getRequirementName = (requirementId: string) => {
    const requirement = requirements.find(r => r.id === requirementId);
    return requirement?.asset_name || 'Unknown Requirement';
  };

  // Get latest validation for artifact
  const getLatestValidation = (artifactId: string) => {
    return validations
      .filter(v => v.artifact_id === artifactId)
      .sort((a, b) => new Date(b.validated_at).getTime() - new Date(a.validated_at).getTime())[0];
  };

  // Table columns configuration
  const columns: ColumnsType<AssetArtifact> = [
    {
      title: 'Artifact',
      key: 'artifact',
      width: 300,
      render: (_, record) => {
        const typeConfig = assetTypeConfig[record.artifact_type];
        return (
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <span style={{ color: typeConfig.color }}>{typeConfig.icon}</span>
              <Text strong className="text-sm">{record.artifact_name}</Text>
              {record.ai_enhanced && (
                <Tag color="cyan" size="small" icon={<RobotOutlined />}>AI</Tag>
              )}
            </div>
            <div className="flex flex-wrap gap-1">
              <Tag color={typeConfig.color} size="small">
                {record.artifact_type}
              </Tag>
              <Tag size="small">{record.artifact_format}</Tag>
              {record.tags.slice(0, 2).map(tag => (
                <Tag key={tag} size="small" color="blue">{tag}</Tag>
              ))}
              {record.tags.length > 2 && (
                <Tag size="small">+{record.tags.length - 2}</Tag>
              )}
            </div>
            <Text type="secondary" className="text-xs">
              {getRequirementName(record.requirement_id)}
            </Text>
          </div>
        );
      }
    },
    {
      title: 'Quality Metrics',
      key: 'quality',
      width: 200,
      render: (_, record) => (
        <div className="space-y-2">
          <div>
            <Text className="text-xs text-gray-500">Quality Score</Text>
            <Progress 
              percent={record.quality_score * 100} 
              size="small"
              status={record.quality_score >= 0.8 ? 'success' : 
                     record.quality_score >= 0.6 ? 'normal' : 'exception'}
              format={percent => `${(percent! / 100).toFixed(2)}`}
            />
          </div>
          <div>
            <Text className="text-xs text-gray-500">Business Value</Text>
            <Progress 
              percent={record.business_value_score * 100} 
              size="small"
              strokeColor="#52c41a"
              format={percent => `${(percent! / 100).toFixed(2)}`}
            />
          </div>
          <div>
            <Text className="text-xs text-gray-500">Actionability</Text>
            <Progress 
              percent={record.actionability_score * 100} 
              size="small"
              strokeColor="#1890ff"
              format={percent => `${(percent! / 100).toFixed(2)}`}
            />
          </div>
        </div>
      )
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 150,
      render: (status: string, record) => {
        const config = statusConfig[status as keyof typeof statusConfig];
        const validation = getLatestValidation(record.id);
        
        return (
          <div className="space-y-1">
            <Tag 
              color={config.color} 
              icon={config.icon}
              className="w-full text-center"
            >
              {status.replace('_', ' ').toUpperCase()}
            </Tag>
            {validation && (
              <Tooltip title={`Last validation: ${validation.feedback.substring(0, 100)}...`}>
                <div className="text-xs text-gray-500">
                  {validation.passed ? '✅' : '❌'} Validated {' '}
                  {new Date(validation.validated_at).toLocaleDateString()}
                </div>
              </Tooltip>
            )}
          </div>
        );
      }
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (date: string) => (
        <div className="text-sm">
          <div>{new Date(date).toLocaleDateString()}</div>
          <div className="text-xs text-gray-500">
            {new Date(date).toLocaleTimeString()}
          </div>
        </div>
      )
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 200,
      render: (_, record) => (
        <Space direction="vertical" size="small" className="w-full">
          <Space size="small">
            <Button 
              size="small" 
              icon={<EyeOutlined />}
              onClick={() => setSelectedArtifact(record)}
            >
              View
            </Button>
            <Button 
              size="small" 
              icon={<DownloadOutlined />}
              onClick={() => handleDownloadArtifact(record)}
            >
              Download
            </Button>
          </Space>
          
          {enableQualityActions && (
            <Space size="small">
              {record.status === 'requires_human_review' && (
                <Button 
                  size="small" 
                  type="primary"
                  icon={<CheckCircleOutlined />}
                  onClick={() => handleApproveArtifact(record.id)}
                >
                  Approve
                </Button>
              )}
              
              {enableAIEnhancement && record.status === 'needs_improvement' && (
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
            </Space>
          )}
        </Space>
      )
    }
  ];

  return (
    <div className="asset-artifacts-list space-y-4">
      {/* Filters and Search */}
      <Card>
        <div className="flex flex-wrap gap-4 items-center justify-between">
          <div className="flex flex-wrap gap-4 items-center">
            <Search
              placeholder="Search artifacts..."
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              style={{ width: 300 }}
              prefix={<SearchOutlined />}
            />
            
            <Select
              value={statusFilter}
              onChange={setStatusFilter}
              style={{ width: 150 }}
              placeholder="Filter by status"
            >
              <Option value="all">All Statuses</Option>
              <Option value="draft">Draft</Option>
              <Option value="approved">Approved</Option>
              <Option value="needs_improvement">Needs Improvement</Option>
              <Option value="requires_human_review">Human Review</Option>
            </Select>
            
            <Select
              value={typeFilter}
              onChange={setTypeFilter}
              style={{ width: 150 }}
              placeholder="Filter by type"
            >
              <Option value="all">All Types</Option>
              <Option value="document">Document</Option>
              <Option value="data">Data</Option>
              <Option value="design">Design</Option>
              <Option value="code">Code</Option>
              <Option value="presentation">Presentation</Option>
            </Select>
          </div>
          
          <div className="flex items-center space-x-2">
            <Badge count={filteredArtifacts.length} showZero>
              <Button icon={<FilterOutlined />}>
                Filtered Results
              </Button>
            </Badge>
            <Button 
              type="primary" 
              icon={<ThunderboltOutlined />}
              onClick={loadArtifacts}
            >
              Refresh
            </Button>
          </div>
        </div>
      </Card>

      {/* Summary Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        {Object.entries(assetTypeConfig).map(([type, config]) => {
          const count = filteredArtifacts.filter(a => a.artifact_type === type).length;
          const avgQuality = filteredArtifacts
            .filter(a => a.artifact_type === type)
            .reduce((sum, a) => sum + a.quality_score, 0) / (count || 1);
          
          return (
            <Card key={type} size="small" className="text-center">
              <div className="space-y-2">
                <div style={{ color: config.color, fontSize: '24px' }}>
                  {config.icon}
                </div>
                <div className="text-lg font-bold">{count}</div>
                <div className="text-sm text-gray-600">{type}</div>
                <div className="text-xs text-gray-500">
                  Avg Quality: {avgQuality.toFixed(2)}
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Artifacts Table */}
      <Card title={`📦 Asset Artifacts (${filteredArtifacts.length})`}>
        <Table
          dataSource={filteredArtifacts}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `${range[0]}-${range[1]} of ${total} artifacts`
          }}
          scroll={{ x: 'max-content' }}
          rowClassName={(record) => {
            if (record.status === 'approved') return 'bg-green-50';
            if (record.status === 'requires_human_review') return 'bg-red-50';
            if (record.status === 'needs_improvement') return 'bg-yellow-50';
            return '';
          }}
        />
      </Card>

      {/* Artifact Detail Modal */}
      <Modal
        title={
          <div className="flex items-center space-x-2">
            {selectedArtifact && (
              <>
                <span style={{ color: assetTypeConfig[selectedArtifact.artifact_type].color }}>
                  {assetTypeConfig[selectedArtifact.artifact_type].icon}
                </span>
                <span>{selectedArtifact.artifact_name}</span>
                {selectedArtifact.ai_enhanced && (
                  <Tag color="cyan" icon={<RobotOutlined />}>AI Enhanced</Tag>
                )}
              </>
            )}
          </div>
        }
        open={!!selectedArtifact}
        onCancel={() => setSelectedArtifact(null)}
        width={900}
        footer={selectedArtifact && [
          <Button key="download" icon={<DownloadOutlined />} onClick={() => handleDownloadArtifact(selectedArtifact)}>
            Download
          </Button>,
          <Button key="close" onClick={() => setSelectedArtifact(null)}>
            Close
          </Button>,
          selectedArtifact.status === 'requires_human_review' && enableQualityActions && (
            <Button 
              key="approve"
              type="primary"
              icon={<CheckCircleOutlined />}
              onClick={() => {
                handleApproveArtifact(selectedArtifact.id);
                setSelectedArtifact(null);
              }}
            >
              Approve
            </Button>
          ),
          selectedArtifact.status === 'needs_improvement' && enableAIEnhancement && (
            <Button 
              key="enhance"
              type="primary"
              ghost
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
          <div className="space-y-6">
            {/* Artifact Metadata */}
            <Descriptions column={2} size="small" bordered>
              <Descriptions.Item label="Type">
                <Tag color={assetTypeConfig[selectedArtifact.artifact_type].color}>
                  {selectedArtifact.artifact_type}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Format">
                {selectedArtifact.artifact_format}
              </Descriptions.Item>
              <Descriptions.Item label="Status">
                <Tag color={statusConfig[selectedArtifact.status].color} icon={statusConfig[selectedArtifact.status].icon}>
                  {selectedArtifact.status.replace('_', ' ').toUpperCase()}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="AI Enhanced">
                {selectedArtifact.ai_enhanced ? (
                  <Tag color="cyan" icon={<RobotOutlined />}>Yes</Tag>
                ) : (
                  <Tag color="default">No</Tag>
                )}
              </Descriptions.Item>
              <Descriptions.Item label="Created">
                {new Date(selectedArtifact.created_at).toLocaleString()}
              </Descriptions.Item>
              <Descriptions.Item label="Last Updated">
                {new Date(selectedArtifact.updated_at).toLocaleString()}
              </Descriptions.Item>
            </Descriptions>

            {/* Quality Metrics */}
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-sm text-gray-500 mb-1">Quality Score</div>
                <Progress 
                  type="circle" 
                  percent={selectedArtifact.quality_score * 100}
                  size={80}
                  format={percent => `${(percent! / 100).toFixed(2)}`}
                />
              </div>
              <div className="text-center">
                <div className="text-sm text-gray-500 mb-1">Business Value</div>
                <Progress 
                  type="circle" 
                  percent={selectedArtifact.business_value_score * 100}
                  size={80}
                  strokeColor="#52c41a"
                  format={percent => `${(percent! / 100).toFixed(2)}`}
                />
              </div>
              <div className="text-center">
                <div className="text-sm text-gray-500 mb-1">Actionability</div>
                <Progress 
                  type="circle" 
                  percent={selectedArtifact.actionability_score * 100}
                  size={80}
                  strokeColor="#1890ff"
                  format={percent => `${(percent! / 100).toFixed(2)}`}
                />
              </div>
            </div>

            {/* Tags */}
            {selectedArtifact.tags.length > 0 && (
              <div>
                <div className="text-sm font-medium text-gray-700 mb-2">Tags</div>
                <Space wrap>
                  {selectedArtifact.tags.map(tag => (
                    <Tag key={tag} color="blue">{tag}</Tag>
                  ))}
                </Space>
              </div>
            )}

            {/* Latest Validation */}
            {(() => {
              const validation = getLatestValidation(selectedArtifact.id);
              return validation && (
                <div>
                  <div className="text-sm font-medium text-gray-700 mb-2">Latest Quality Validation</div>
                  <Alert
                    message={`Validation ${validation.passed ? 'Passed' : 'Failed'} (Score: ${validation.score.toFixed(3)})`}
                    description={validation.feedback}
                    type={validation.passed ? 'success' : 'warning'}
                    showIcon
                  />
                  {validation.improvement_suggestions.length > 0 && (
                    <div className="mt-2">
                      <div className="text-xs font-medium text-gray-600 mb-1">Improvement Suggestions:</div>
                      <ul className="list-disc list-inside text-xs text-gray-600">
                        {validation.improvement_suggestions.map((suggestion, index) => (
                          <li key={index}>{suggestion}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              );
            })()}

            {/* Content Preview */}
            <div>
              <div className="text-sm font-medium text-gray-700 mb-2">Content Preview</div>
              <div className="bg-gray-50 p-4 rounded border max-h-64 overflow-y-auto">
                <Paragraph
                  className="mb-0 text-sm whitespace-pre-wrap"
                  ellipsis={{ rows: 10, expandable: true, symbol: 'Show more' }}
                >
                  {selectedArtifact.content || 'No content available'}
                </Paragraph>
              </div>
            </div>

            {/* Pillar Compliance */}
            {selectedArtifact.pillar_compliance && Object.keys(selectedArtifact.pillar_compliance).length > 0 && (
              <div>
                <div className="text-sm font-medium text-gray-700 mb-2">Pillar Compliance</div>
                <div className="grid grid-cols-2 gap-2">
                  {Object.entries(selectedArtifact.pillar_compliance).map(([pillar, compliant]) => (
                    <div key={pillar} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                      <span className="text-xs">{pillar.replace('_', ' ')}</span>
                      {compliant ? (
                        <CheckCircleOutlined className="text-green-500" />
                      ) : (
                        <ExclamationCircleOutlined className="text-red-500" />
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};