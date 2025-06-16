// frontend/src/hooks/useAssetRefinementStatus.ts
// Hook per tracking delle richieste di modifica asset

import { useState, useEffect, useCallback } from 'react';

interface EnhancementTask {
  id: string;
  name: string;
  description: string;
  status: string;
  created_at: string;
  metadata?: {
    original_task_id?: string;
    refinement_type?: string;
    user_feedback?: string;
    asset_data?: any;
    improvement_focus?: string;
    iteration_count?: number;
  };
  priority: number;
  assigned_to_role: string;
}

interface AssetRefinementStatus {
  pendingRefinements: EnhancementTask[];
  completedRefinements: EnhancementTask[];
  totalRefinements: number;
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

export const useAssetRefinementStatus = (workspaceId: string, assetName?: string): AssetRefinementStatus => {
  const [status, setStatus] = useState<Omit<AssetRefinementStatus, 'refresh'>>({
    pendingRefinements: [],
    completedRefinements: [],
    totalRefinements: 0,
    isLoading: true,
    error: null
  });

  const fetchRefinementStatus = useCallback(async () => {
    if (!workspaceId) {
      setStatus(prev => ({ ...prev, isLoading: false }));
      return;
    }

    try {
      setStatus(prev => ({ ...prev, isLoading: true, error: null }));

      // Fetch all enhancement tasks for the workspace
      const response = await fetch(`http://localhost:8000/api/workspaces/${workspaceId}/tasks?task_type=asset_enhancement`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch enhancement tasks: ${response.statusText}`);
      }

      const tasks: EnhancementTask[] = await response.json();
      
      console.log(`📊 [useAssetRefinementStatus] Fetched ${tasks.length} enhancement tasks for workspace ${workspaceId}`);
      console.log('📋 Enhancement tasks:', tasks);

      // Filter tasks by asset name if provided
      let relevantTasks = tasks;
      if (assetName) {
        console.log(`🔍 Filtering tasks for asset: ${assetName}`);
        relevantTasks = tasks.filter(task => {
          // Check if task name contains the asset name (handling "🔄 ENHANCE: " prefix)
          const taskNameLower = task.name.toLowerCase();
          const assetNameLower = assetName.toLowerCase();
          
          const matchByName = taskNameLower.includes(assetNameLower) || 
                            taskNameLower.includes(`enhance: ${assetNameLower}`) ||
                            taskNameLower.includes(`🔄 enhance: ${assetNameLower}`);
          
          // Check metadata
          const matchByMetadata = task.metadata?.asset_data?.name === assetName ||
                                task.metadata?.asset_data?.asset_name === assetName;
          
          // Check description
          const matchByDescription = task.description.toLowerCase().includes(assetNameLower);
          
          // Also check if the task type is asset_enhancement
          const isEnhancementTask = task.metadata?.refinement_type === 'user_requested' ||
                                  task.description.includes('User-requested enhancement');
          
          if (matchByName || matchByMetadata || matchByDescription || isEnhancementTask) {
            console.log(`✅ Task ${task.id} matches asset ${assetName}:`, {
              name: task.name,
              matchByName,
              matchByMetadata,
              matchByDescription,
              isEnhancementTask
            });
            return true;
          }
          return false;
        });
        console.log(`📌 Found ${relevantTasks.length} tasks for asset ${assetName}`);
      }

      // Separate pending and completed (include failed tasks in history)
      const pendingRefinements = relevantTasks.filter(task => 
        task.status === 'pending' || task.status === 'in_progress'
      );
      
      const completedRefinements = relevantTasks.filter(task => 
        task.status === 'completed' || task.status === 'failed'
      );

      setStatus({
        pendingRefinements,
        completedRefinements,
        totalRefinements: relevantTasks.length,
        isLoading: false,
        error: null
      });

    } catch (error) {
      console.error('Error fetching refinement status:', error);
      setStatus(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to fetch refinement status'
      }));
    }
  }, [workspaceId, assetName]);

  useEffect(() => {
    fetchRefinementStatus();
    
    // Refresh every 30 seconds to track progress
    const interval = setInterval(fetchRefinementStatus, 30000);
    
    return () => clearInterval(interval);
  }, [fetchRefinementStatus]);

  return {
    ...status,
    refresh: fetchRefinementStatus
  };
};