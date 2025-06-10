'use client';

import React, { useState, useEffect } from 'react';
import { api } from '@/utils/api';

interface WorkflowRule {
  id: string;
  name: string;
  description: string;
  trigger: WorkflowTrigger;
  conditions: WorkflowCondition[];
  actions: WorkflowAction[];
  enabled: boolean;
  created_at: string;
  last_triggered?: string;
  execution_count: number;
  success_rate: number;
}

interface WorkflowTrigger {
  type: 'asset_updated' | 'dependency_detected' | 'quality_threshold' | 'time_based' | 'user_action';
  config: any;
}

interface WorkflowCondition {
  type: 'impact_score' | 'domain_match' | 'asset_type' | 'quality_score' | 'time_window' | 'user_approval';
  operator: 'gt' | 'lt' | 'eq' | 'in' | 'not_in' | 'exists';
  value: any;
}

interface WorkflowAction {
  type: 'update_dependencies' | 'notify_users' | 'create_task' | 'batch_update' | 'quality_enhance' | 'generate_report';
  config: any;
  delay_seconds?: number;
}

interface AutomationTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  complexity: 'simple' | 'intermediate' | 'advanced';
  template: Partial<WorkflowRule>;
  use_cases: string[];
  estimated_time_saving: string;
}

const AUTOMATION_TEMPLATES: AutomationTemplate[] = [
  {
    id: 'auto_dependency_updates',
    name: 'Auto Dependency Updates',
    description: 'Automatically update low-impact dependencies when source assets change',
    category: 'efficiency',
    complexity: 'simple',
    template: {
      trigger: { type: 'dependency_detected', config: {} },
      conditions: [
        { type: 'impact_score', operator: 'lt', value: 0.3 },
        { type: 'quality_score', operator: 'gt', value: 0.8 }
      ],
      actions: [
        { type: 'update_dependencies', config: { auto_apply: true } }
      ]
    },
    use_cases: ['Routine data updates', 'Template refreshes', 'Style guide changes'],
    estimated_time_saving: '2-4 hours/week'
  },
  {
    id: 'quality_enhancement_pipeline',
    name: 'Quality Enhancement Pipeline', 
    description: 'Automatically enhance asset quality when thresholds are met',
    category: 'quality',
    complexity: 'intermediate',
    template: {
      trigger: { type: 'asset_updated', config: {} },
      conditions: [
        { type: 'quality_score', operator: 'lt', value: 0.7 },
        { type: 'asset_type', operator: 'in', value: ['analysis', 'report', 'strategy'] }
      ],
      actions: [
        { type: 'quality_enhance', config: { ai_suggestions: true } },
        { type: 'notify_users', config: { roles: ['reviewer'] } }
      ]
    },
    use_cases: ['Content quality control', 'Report standardization', 'Analysis validation'],
    estimated_time_saving: '3-6 hours/week'
  },
  {
    id: 'cross_domain_sync',
    name: 'Cross-Domain Synchronization',
    description: 'Sync changes across related domains automatically',
    category: 'integration',
    complexity: 'advanced',
    template: {
      trigger: { type: 'asset_updated', config: {} },
      conditions: [
        { type: 'domain_match', operator: 'in', value: ['finance', 'marketing'] },
        { type: 'impact_score', operator: 'gt', value: 0.6 }
      ],
      actions: [
        { type: 'create_task', config: { target_domains: 'affected', priority: 'medium' } },
        { type: 'batch_update', config: { group_similar: true }, delay_seconds: 300 }
      ]
    },
    use_cases: ['Financial planning updates', 'Marketing campaign sync', 'Strategic alignment'],
    estimated_time_saving: '5-10 hours/week'
  }
];

interface Props {
  workspaceId: string;
  className?: string;
}

export const WorkflowAutomationEngine: React.FC<Props> = ({
  workspaceId,
  className = ''
}) => {
  const [rules, setRules] = useState<WorkflowRule[]>([]);
  const [templates, setTemplates] = useState<AutomationTemplate[]>(AUTOMATION_TEMPLATES);
  const [selectedTemplate, setSelectedTemplate] = useState<AutomationTemplate | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [automationStats, setAutomationStats] = useState({
    total_rules: 0,
    active_rules: 0,
    total_executions: 0,
    time_saved_hours: 0,
    avg_success_rate: 0
  });

  useEffect(() => {
    loadWorkflowRules();
    loadAutomationStats();
  }, [workspaceId]);

  const loadWorkflowRules = async () => {
    try {
      const response = await api.workflowAutomation.getRules(workspaceId);
      setRules(response.rules || []);
    } catch (error) {
      console.error('Failed to load workflow rules:', error);
    }
  };

  const loadAutomationStats = async () => {
    try {
      const response = await api.workflowAutomation.getStats(workspaceId);
      setAutomationStats(response);
    } catch (error) {
      console.error('Failed to load automation stats:', error);
    }
  };

  const createRuleFromTemplate = async (template: AutomationTemplate) => {
    try {
      setIsCreating(true);
      
      const newRule: Partial<WorkflowRule> = {
        name: template.name,
        description: template.description,
        ...template.template,
        enabled: true
      };

      const response = await api.workflowAutomation.createRule(workspaceId, newRule);
      setRules(prev => [response, ...prev]);
      setSelectedTemplate(null);
      setIsCreating(false);
      
    } catch (error) {
      console.error('Failed to create rule:', error);
      setIsCreating(false);
    }
  };

  const toggleRule = async (ruleId: string, enabled: boolean) => {
    try {
      await api.workflowAutomation.updateRule(ruleId, { enabled });
      setRules(prev => prev.map(rule => 
        rule.id === ruleId ? { ...rule, enabled } : rule
      ));
    } catch (error) {
      console.error('Failed to toggle rule:', error);
    }
  };

  const deleteRule = async (ruleId: string) => {
    try {
      await api.workflowAutomation.deleteRule(ruleId);
      setRules(prev => prev.filter(rule => rule.id !== ruleId));
    } catch (error) {
      console.error('Failed to delete rule:', error);
    }
  };

  const getTriggerIcon = (type: string) => {
    switch (type) {
      case 'asset_updated': return '📝';
      case 'dependency_detected': return '🔗';
      case 'quality_threshold': return '📊';
      case 'time_based': return '⏰';
      default: return '⚡';
    }
  };

  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'simple': return 'bg-green-100 text-green-800';
      case 'intermediate': return 'bg-yellow-100 text-yellow-800';
      case 'advanced': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className={`bg-white rounded-lg border border-gray-200 ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">🤖 Workflow Automation</h2>
            <p className="text-sm text-gray-600">Automate asset management workflows to save time and improve consistency</p>
          </div>
          <button
            onClick={() => setSelectedTemplate(templates[0])}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Create Automation
          </button>
        </div>
      </div>

      {/* Stats Dashboard */}
      <div className="px-6 py-4 bg-gradient-to-r from-purple-50 to-blue-50 border-b border-gray-200">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-700">{automationStats.active_rules}</div>
            <div className="text-sm text-purple-600">Active Rules</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-700">{automationStats.total_executions}</div>
            <div className="text-sm text-blue-600">Executions</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-700">{automationStats.time_saved_hours}h</div>
            <div className="text-sm text-green-600">Time Saved</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-indigo-700">{automationStats.avg_success_rate}%</div>
            <div className="text-sm text-indigo-600">Success Rate</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-pink-700">{rules.length}</div>
            <div className="text-sm text-pink-600">Total Rules</div>
          </div>
        </div>
      </div>

      {/* Active Rules */}
      <div className="px-6 py-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Active Automation Rules</h3>
        
        {rules.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <div className="text-4xl mb-4">🤖</div>
            <p className="mb-4">No automation rules configured yet</p>
            <button
              onClick={() => setSelectedTemplate(templates[0])}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Create Your First Rule
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {rules.map((rule) => (
              <div key={rule.id} className={`border rounded-lg p-4 ${rule.enabled ? 'border-green-200 bg-green-50' : 'border-gray-200 bg-gray-50'}`}>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <span className="text-lg">{getTriggerIcon(rule.trigger.type)}</span>
                      <h4 className="font-medium text-gray-900">{rule.name}</h4>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        rule.enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {rule.enabled ? 'Active' : 'Disabled'}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-3">{rule.description}</p>
                    
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="font-medium text-gray-700">Executions:</span>
                        <span className="ml-1 text-gray-600">{rule.execution_count}</span>
                      </div>
                      <div>
                        <span className="font-medium text-gray-700">Success Rate:</span>
                        <span className="ml-1 text-gray-600">{rule.success_rate}%</span>
                      </div>
                      <div>
                        <span className="font-medium text-gray-700">Conditions:</span>
                        <span className="ml-1 text-gray-600">{rule.conditions.length}</span>
                      </div>
                      <div>
                        <span className="font-medium text-gray-700">Actions:</span>
                        <span className="ml-1 text-gray-600">{rule.actions.length}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2 ml-4">
                    <button
                      onClick={() => toggleRule(rule.id, !rule.enabled)}
                      className={`px-3 py-1 text-xs font-medium rounded transition-colors ${
                        rule.enabled 
                          ? 'bg-red-100 text-red-700 hover:bg-red-200' 
                          : 'bg-green-100 text-green-700 hover:bg-green-200'
                      }`}
                    >
                      {rule.enabled ? 'Disable' : 'Enable'}
                    </button>
                    <button
                      onClick={() => deleteRule(rule.id)}
                      className="px-3 py-1 text-xs font-medium text-red-700 bg-red-100 rounded hover:bg-red-200 transition-colors"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Template Selection Modal */}
      {selectedTemplate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-auto">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">Choose Automation Template</h3>
                <button
                  onClick={() => setSelectedTemplate(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {templates.map((template) => (
                  <div
                    key={template.id}
                    className={`border rounded-lg p-4 cursor-pointer transition-all hover:shadow-md ${
                      selectedTemplate.id === template.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                    }`}
                    onClick={() => setSelectedTemplate(template)}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium text-gray-900">{template.name}</h4>
                      <span className={`px-2 py-1 text-xs rounded-full ${getComplexityColor(template.complexity)}`}>
                        {template.complexity}
                      </span>
                    </div>
                    
                    <p className="text-sm text-gray-600 mb-3">{template.description}</p>
                    
                    <div className="text-xs text-gray-500 mb-3">
                      <strong>Time Saving:</strong> {template.estimated_time_saving}
                    </div>
                    
                    <div className="text-xs text-gray-500">
                      <strong>Use Cases:</strong>
                      <ul className="list-disc list-inside mt-1">
                        {template.use_cases.slice(0, 2).map((useCase, index) => (
                          <li key={index}>{useCase}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                ))}
              </div>
              
              {selectedTemplate && (
                <div className="mt-6 pt-6 border-t border-gray-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium text-gray-900 mb-1">{selectedTemplate.name}</h4>
                      <p className="text-sm text-gray-600">{selectedTemplate.description}</p>
                    </div>
                    <button
                      onClick={() => createRuleFromTemplate(selectedTemplate)}
                      disabled={isCreating}
                      className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                    >
                      {isCreating ? 'Creating...' : 'Create Rule'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};