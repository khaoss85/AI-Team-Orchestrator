import { useState, useEffect, useCallback } from 'react';
import { api } from '@/utils/api';
import type { AgentProposal, OrchestrationStats } from '@/types';

export const useOrchestration = (workspaceId: string) => {
  const [proposals, setProposals] = useState<AgentProposal[]>([]);
  const [stats, setStats] = useState<OrchestrationStats>({
    total: 0,
    pending: 0,
    implementing: 0,
    completed: 0,
    avgConfidence: 0,
    totalEstimatedValue: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProposals = useCallback(async () => {
    try {
      setLoading(true);
      const tasksResponse = await api.monitoring.getWorkspaceTasks(workspaceId, {
        status: 'completed',
        limit: 50
      });
      const tasksArray = Array.isArray(tasksResponse)
        ? tasksResponse
        : Array.isArray(tasksResponse?.tasks)
          ? tasksResponse.tasks
          : [];

      const proposalsData = await Promise.all(
        tasksArray
          .filter(task => task.result && isViableProposal(task))
          .map(task => transformTaskToProposal(task, workspaceId))
      );
      setProposals(proposalsData);
      updateStats(proposalsData);
      setError(null);
    } catch (err) {
      console.error('Error fetching proposals:', err);
      setError(err instanceof Error ? err.message : 'Failed to load proposals');
    } finally {
      setLoading(false);
    }
  }, [workspaceId]);

  const isViableProposal = (task: any): boolean => {
    if (!task.result) return false;
    const hasActionableOutput =
      task.result.actionable_assets ||
      task.result.next_steps ||
      task.result.recommendations ||
      (task.result.output && task.result.output.length > 100);
    const hasQualityIndicators =
      task.result.confidence_score ||
      task.result.validation_score ||
      task.status === 'completed';
    return hasActionableOutput && hasQualityIndicators;
  };

  const transformTaskToProposal = async (task: any, workspaceId: string): Promise<AgentProposal> => {
    const agents = await api.agents.list(workspaceId);
    const agent = agents.find(a => a.id === task.agent_id);
    const proposalType = determineProposalType(task);
    const preview = generatePreview(task, proposalType);
    const output = extractActionableOutput(task);
    const nextSteps = generateNextSteps(task, proposalType);

    return {
      id: `proposal_${task.id}`,
      agentName: agent?.name || 'Unknown Agent',
      agentRole: agent?.role || 'Agent',
      title: extractTitle(task),
      type: proposalType,
      status: 'ready_for_review',
      confidence: calculateConfidence(task),
      timestamp: getRelativeTime(task.updated_at),
      taskId: task.id,
      preview,
      output,
      nextSteps,
      metadata: {
        createdAt: task.created_at,
        updatedAt: task.updated_at,
        sourceTaskId: task.id,
        estimatedValue: calculateEstimatedValue(task),
        riskLevel: calculateRiskLevel(task)
      }
    };
  };

  const determineProposalType = (task: any): AgentProposal['type'] => {
    const taskName = task.name.toLowerCase();
    const content = (task.result?.output || '').toLowerCase();
    if (taskName.includes('analy') || content.includes('insight')) return 'analysis';
    if (taskName.includes('optim') || content.includes('improve')) return 'optimization';
    if (taskName.includes('system') || taskName.includes('automat')) return 'system';
    return 'deliverable';
  };

  const generatePreview = (task: any, type: string) => {
    const result = task.result;
    if (result.actionable_assets) {
      return {
        type: 'dataset' as const,
        data: `${Object.keys(result.actionable_assets).length} asset pronti per l'uso`
      };
    }
    if (type === 'analysis') {
      return {
        type: 'chart' as const,
        data: result.summary || 'Analisi completata con insights azionabili'
      };
    }
    return {
      type: 'document' as const,
      data: result.summary || task.description || 'Output completato'
    };
  };

  const extractActionableOutput = (task: any) => {
    const result = task.result;
    return {
      summary: result.summary || result.output || 'Risultato completato',
      actionable: result.actionable_assets
        ? `${Object.keys(result.actionable_assets).length} asset business-ready`
        : result.deliverables?.join(', ') || 'Output strutturato disponibile',
      impact: result.estimated_impact || result.business_value || 'Impatto da valutare',
      technicalDetails: result
    };
  };

  const generateNextSteps = (task: any, type: string) => {
    const steps = [] as Array<{action: string; urgency: 'high' | 'medium' | 'low'; effort: 'low' | 'medium' | 'high'; automated?: boolean}>;
    if (task.result?.next_steps) {
      return task.result.next_steps.map((step: string, index: number) => ({
        action: step,
        urgency: index === 0 ? 'high' : 'medium',
        effort: 'medium'
      }));
    }
    switch (type) {
      case 'analysis':
        steps.push(
          { action: 'Implementa insights trovati', urgency: 'high', effort: 'medium' },
          { action: 'Monitora metriche impatto', urgency: 'medium', effort: 'low' }
        );
        break;
      case 'deliverable':
        steps.push(
          { action: 'Scarica e implementa asset', urgency: 'high', effort: 'low' },
          { action: 'Configura monitoraggio', urgency: 'medium', effort: 'medium' }
        );
        break;
      default:
        steps.push({ action: 'Revisiona output', urgency: 'medium', effort: 'low' });
    }
    return steps;
  };

  const calculateConfidence = (task: any): number => {
    let confidence = 70;
    if (task.result?.confidence_score) {
      confidence = task.result.confidence_score * 100;
    } else {
      if (task.result?.actionable_assets) confidence += 20;
      if (task.result?.next_steps?.length > 0) confidence += 10;
      if (task.result?.summary?.length > 100) confidence += 10;
      if (task.status === 'completed') confidence += 10;
    }
    return Math.min(100, Math.max(0, confidence));
  };

  const calculateEstimatedValue = (task: any): number => {
    if (task.result?.estimated_value) return task.result.estimated_value;
    if (task.result?.business_impact?.match(/\€(\d+)/)) {
      return parseInt(task.result.business_impact.match(/\€(\d+)/)[1]);
    }
    return 0;
  };

  const calculateRiskLevel = (task: any): 'low' | 'medium' | 'high' => {
    const confidence = calculateConfidence(task);
    if (confidence > 85) return 'low';
    if (confidence > 65) return 'medium';
    return 'high';
  };

  const extractTitle = (task: any): string => {
    if (task.result?.title) return task.result.title;
    const name = task.name;
    return name
      .replace(/^(PRODUCE ASSET:|CREATE:|ANALYZE:|DEVELOP:)/gi, '')
      .replace(/^Task:\s*/gi, '')
      .trim();
  };

  const getRelativeTime = (timestamp: string): string => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffMs = now.getTime() - time.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    if (diffHours < 1) return "Meno di un'ora fa";
    if (diffHours < 24) return `${diffHours} ore fa`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays} giorni fa`;
  };

  const updateStats = (proposalsData: AgentProposal[]) => {
    const newStats: OrchestrationStats = {
      total: proposalsData.length,
      pending: proposalsData.filter(p => p.status === 'ready_for_review').length,
      implementing: proposalsData.filter(p => p.status === 'implementing').length,
      completed: proposalsData.filter(p => p.status === 'completed').length,
      avgConfidence:
        proposalsData.length > 0
          ? Math.round(proposalsData.reduce((acc, p) => acc + p.confidence, 0) / proposalsData.length)
          : 0,
      totalEstimatedValue: proposalsData.reduce((acc, p) => acc + (p.metadata.estimatedValue || 0), 0)
    };
    setStats(newStats);
  };

  const approveProposal = useCallback(async (proposalId: string) => {
    try {
      setProposals(prev => prev.map(p => (p.id === proposalId ? { ...p, status: 'implementing' } : p)));
      setTimeout(() => {
        setProposals(prev => prev.map(p => (p.id === proposalId ? { ...p, status: 'completed' } : p)));
      }, 3000);
      return true;
    } catch (error) {
      console.error('Error approving proposal:', error);
      return false;
    }
  }, []);

  const rejectProposal = useCallback(async (proposalId: string, reason?: string) => {
    try {
      setProposals(prev => prev.map(p => (p.id === proposalId ? { ...p, status: 'rejected' } : p)));
      return true;
    } catch (error) {
      console.error('Error rejecting proposal:', error);
      return false;
    }
  }, []);

  useEffect(() => {
    if (workspaceId) {
      fetchProposals();
      const interval = setInterval(fetchProposals, 30000);
      return () => clearInterval(interval);
    }
  }, [workspaceId, fetchProposals]);

  return {
    proposals,
    stats,
    loading,
    error,
    actions: {
      refresh: fetchProposals,
      approve: approveProposal,
      reject: rejectProposal
    }
  };
};

