// frontend/src/hooks/useProjectResults.ts - UNIFIED PROJECT RESULTS HOOK

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/utils/api';
import { ProjectDeliverablesExtended, ActionableAsset } from '@/types';

export interface UnifiedResultItem {
  // Common fields
  id: string;
  title: string;
  description: string;
  type: 'asset' | 'deliverable' | 'strategy' | 'analysis' | 'content';
  category: string;
  
  // Quality indicators
  actionabilityScore: number;
  validationScore: number;
  readyToUse: boolean;
  businessImpact: 'low' | 'medium' | 'high' | 'critical';
  
  // Content
  visualSummary?: string;
  keyInsights: string[];
  nextActions?: string[];
  metrics: Record<string, any>;
  structuredContent?: any;
  
  // Usage
  usageInstructions?: string;
  downloadable: boolean;
  automationReady: boolean;
  
  // Metadata
  sourceTaskId: string;
  sourceTaskName: string;
  agentName: string;
  agentRole: string;
  createdAt: Date;
  lastUpdated: Date;
  
  // Actions
  actions: {
    canView: boolean;
    canDownload: boolean;
    canUse: boolean;
    canShare: boolean;
  };
}

export interface ProjectResultsState {
  // Data
  allResults: UnifiedResultItem[];
  readyToUse: UnifiedResultItem[];
  inProgress: UnifiedResultItem[];
  finalDeliverables: UnifiedResultItem[];
  
  // Metadata
  totalResults: number;
  completionRate: number;
  qualityScore: number;
  
  // State
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
}

export interface QualityFilters {
  businessReady: boolean;
  highImpact: boolean;
  quickWins: boolean;
  customThreshold?: number;
}

export const useProjectResults = (workspaceId: string) => {
  const [state, setState] = useState<ProjectResultsState>({
    allResults: [],
    readyToUse: [],
    inProgress: [],
    finalDeliverables: [],
    totalResults: 0,
    completionRate: 0,
    qualityScore: 0,
    loading: true,
    error: null,
    lastUpdated: null,
  });

  const debugLog = useCallback((message: string, data?: any) => {
    if (process.env.NODE_ENV === 'development') {
      console.log(`🔄 [useProjectResults] ${message}`, data || '');
    }
  }, []);

  // Normalize different data sources into UnifiedResultItem
  const normalizeAssetToResult = useCallback((asset: ActionableAsset, taskInfo: any): UnifiedResultItem => {
    return {
      id: `asset_${asset.source_task_id}`,
      title: (asset.asset_name || 'Unknown Asset').replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      description: asset.usage_instructions || 'Asset pronto per l\'uso',
      type: 'asset',
      category: (asset.asset_name || '').includes('calendar') ? 'content' : 
                (asset.asset_name || '').includes('database') ? 'data' : 
                (asset.asset_name || '').includes('strategy') ? 'strategy' : 'general',
      
      actionabilityScore: asset.actionability_score || 0.5,
      validationScore: asset.validation_score || 0.5,
      readyToUse: asset.ready_to_use || false,
      businessImpact: asset.actionability_score > 0.8 ? 'high' : 
                     asset.actionability_score > 0.6 ? 'medium' : 'low',
      
      visualSummary: undefined,
      keyInsights: [],
      nextActions: [],
      metrics: {},
      structuredContent: asset.asset_data,
      
      usageInstructions: asset.usage_instructions,
      downloadable: asset.ready_to_use || false,
      automationReady: asset.actionability_score > 0.8,
      
      sourceTaskId: asset.source_task_id,
      sourceTaskName: taskInfo?.task_name || 'Unknown Task',
      agentName: taskInfo?.agent_name || 'AI Team',
      agentRole: taskInfo?.agent_role || 'Specialist',
      createdAt: new Date(),
      lastUpdated: new Date(),
      
      actions: {
        canView: true,
        canDownload: asset.ready_to_use || false,
        canUse: asset.ready_to_use || false,
        canShare: asset.ready_to_use || false,
      }
    };
  }, []);

  const normalizeDeliverableToResult = useCallback((deliverable: any): UnifiedResultItem => {
    // Use structured_content directly (it's already an object, not a JSON string)
    const detailedResults = deliverable.structured_content;
    
    if (detailedResults) {
      console.log('✅ Found structured content for:', deliverable.task_name);
    }
    
    // Extract enhanced data from detailed results
    const extractedInsights = detailedResults?.actionable_insights || 
                             detailedResults?.key_insights || 
                             deliverable.key_insights || [];
    
    const extractedNextActions = detailedResults?.next_steps || 
                                deliverable.next_actions || 
                                deliverable.next_steps || [];
    
    return {
      id: `deliverable_${deliverable.task_id}`,
      title: deliverable.task_name,
      description: deliverable.output.substring(0, 200) + '...',
      type: 'deliverable',
      category: deliverable.type || 'general',
      
      actionabilityScore: 0.9, // Deliverables are generally high quality
      validationScore: 0.9,
      readyToUse: true,
      businessImpact: deliverable.type === 'final_deliverable' ? 'critical' : 'high',
      
      visualSummary: deliverable.visual_summary,
      keyInsights: extractedInsights,
      nextActions: extractedNextActions,
      metrics: deliverable.metrics || {},
      structuredContent: detailedResults || deliverable.structured_content,
      
      usageInstructions: `Risultato di ${deliverable.agent_role}`,
      downloadable: true,
      automationReady: !!deliverable.structured_content,
      
      sourceTaskId: deliverable.task_id,
      sourceTaskName: deliverable.task_name,
      agentName: deliverable.agent_name,
      agentRole: deliverable.agent_role,
      createdAt: new Date(deliverable.created_at),
      lastUpdated: new Date(deliverable.created_at),
      
      actions: {
        canView: true,
        canDownload: true,
        canUse: true,
        canShare: true,
      }
    };
  }, []);

  // Apply quality filters
  const applyQualityFilters = useCallback((results: UnifiedResultItem[], filters: QualityFilters): UnifiedResultItem[] => {
    return results.filter(result => {
      if (filters.businessReady && (!result.readyToUse || result.actionabilityScore < 0.8)) {
        return false;
      }
      
      if (filters.highImpact && result.businessImpact === 'low') {
        return false;
      }
      
      if (filters.quickWins && (!result.readyToUse || !result.automationReady)) {
        return false;
      }
      
      if (filters.customThreshold && result.actionabilityScore < filters.customThreshold) {
        return false;
      }
      
      return true;
    });
  }, []);

  // Fetch and unify all project results
  const fetchProjectResults = useCallback(async () => {
    if (!workspaceId) {
      debugLog('No workspaceId provided, skipping fetch');
      return;
    }

    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      debugLog(`Fetching unified results for workspace: ${workspaceId}`);

      // Fetch both deliverables and assets in parallel
      const [deliverablesResponse, assetsResponse] = await Promise.allSettled([
        api.monitoring.getProjectDeliverables(workspaceId),
        api.monitoring.getAssetTracking(workspaceId)
      ]);

      const allResults: UnifiedResultItem[] = [];

      // Process deliverables
      if (deliverablesResponse.status === 'fulfilled') {
        const deliverables = deliverablesResponse.value;
        
        deliverables.key_outputs.forEach(output => {
          const normalizedResult = normalizeDeliverableToResult(output);
          allResults.push(normalizedResult);
        });
        debugLog(`Processed ${deliverables.key_outputs.length} deliverables`);
      }

      // Process assets (from asset management)
      if (assetsResponse.status === 'fulfilled') {
        const assetData = assetsResponse.value;
        if (assetData?.completed_assets) {
          assetData.completed_assets.forEach((asset: any) => {
            const normalizedResult = normalizeAssetToResult(asset, asset);
            // Avoid duplicates by checking if we already have this task
            const exists = allResults.some(r => r.sourceTaskId === asset.task_id);
            if (!exists) {
              allResults.push(normalizedResult);
            }
          });
          debugLog(`Processed ${assetData.completed_assets.length} assets`);
        }
      }

      // Sort by quality and recency
      allResults.sort((a, b) => {
        // Primary sort: business impact
        const impactOrder = { critical: 4, high: 3, medium: 2, low: 1 };
        const impactDiff = impactOrder[b.businessImpact] - impactOrder[a.businessImpact];
        if (impactDiff !== 0) return impactDiff;
        
        // Secondary sort: actionability score
        const scoreDiff = b.actionabilityScore - a.actionabilityScore;
        if (Math.abs(scoreDiff) > 0.1) return scoreDiff;
        
        // Tertiary sort: recency
        return b.lastUpdated.getTime() - a.lastUpdated.getTime();
      });

      // Categorize results
      const readyToUse = allResults.filter(r => r.readyToUse && r.actionabilityScore >= 0.7);
      const inProgress = allResults.filter(r => !r.readyToUse || r.actionabilityScore < 0.7);
      const finalDeliverables = allResults.filter(r => r.type === 'deliverable' && r.businessImpact === 'critical');

      // Calculate metrics
      const totalResults = allResults.length;
      const completionRate = totalResults > 0 ? (readyToUse.length / totalResults) * 100 : 0;
      const qualityScore = totalResults > 0 ? 
        allResults.reduce((sum, r) => sum + r.actionabilityScore, 0) / totalResults * 100 : 0;

      setState({
        allResults,
        readyToUse,
        inProgress,
        finalDeliverables,
        totalResults,
        completionRate,
        qualityScore,
        loading: false,
        error: null,
        lastUpdated: new Date(),
      });

      debugLog(`Unified results processed: ${totalResults} total, ${readyToUse.length} ready`);

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load project results';
      debugLog('Error fetching unified results:', err);
      
      setState(prev => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }));
    }
  }, [workspaceId, debugLog, normalizeAssetToResult, normalizeDeliverableToResult]);

  // Initialize fetch
  useEffect(() => {
    debugLog('Hook initialized, starting fetch');
    fetchProjectResults();
  }, [fetchProjectResults]);

  // Helper functions
  const getFilteredResults = useCallback((filters: QualityFilters): UnifiedResultItem[] => {
    return applyQualityFilters(state.allResults, filters);
  }, [state.allResults, applyQualityFilters]);

  const getResultsByType = useCallback((type: UnifiedResultItem['type']): UnifiedResultItem[] => {
    return state.allResults.filter(result => result.type === type);
  }, [state.allResults]);

  const getHighImpactResults = useCallback((): UnifiedResultItem[] => {
    return state.allResults.filter(result => 
      result.businessImpact === 'high' || result.businessImpact === 'critical'
    );
  }, [state.allResults]);

  return {
    // Data
    ...state,
    
    // Actions
    refresh: fetchProjectResults,
    
    // Helpers
    getFilteredResults,
    getResultsByType,
    getHighImpactResults,
  };
};