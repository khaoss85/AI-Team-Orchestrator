// frontend/src/hooks/useUnifiedAssets.ts
// Simplified hook that uses the unified backend asset system

import { useState, useEffect, useCallback } from 'react';

interface UnifiedAsset {
  id: string;
  name: string;
  type: string;
  versions: number;
  lastModified: string;
  sourceTaskId: string;
  ready_to_use: boolean;
  quality_scores: {
    overall?: number;
    concreteness?: number;
    actionability?: number;
    completeness?: number;
  };
  content: {
    rendered_html?: string;
    structured_content?: any;
    markup_elements?: any;
    has_ai_enhancement: boolean;
    enhancement_source: string;
  };
  version_history: Array<{
    version: string;
    created_at: string;
    created_by: string;
    task_name: string;
    task_id: string;
    quality_scores: any;
    changes_summary: string;
  }>;
  related_tasks: Array<{
    id: string;
    name: string;
    version: number;
    updated_at: string;
    status: string;
  }>;
}

interface UnifiedAssetsResponse {
  workspace_id: string;
  workspace_goal: string;
  assets: Record<string, UnifiedAsset>;
  asset_count: number;
  total_versions: number;
  processing_timestamp: string;
  data_source: string;
}

interface UseUnifiedAssetsReturn {
  assets: UnifiedAsset[];
  assetsMap: Record<string, UnifiedAsset>;
  loading: boolean;
  error: string | null;
  workspaceGoal: string;
  assetCount: number;
  totalVersions: number;
  refresh: () => Promise<void>;
}

export const useUnifiedAssets = (workspaceId: string): UseUnifiedAssetsReturn => {
  const [data, setData] = useState<UnifiedAssetsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAssets = useCallback(async () => {
    if (!workspaceId) {
      console.log('🔍 [useUnifiedAssets] No workspaceId provided');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      console.log('🔍 [useUnifiedAssets] Fetching unified assets for workspace:', workspaceId);
      console.log('🔍 [useUnifiedAssets] Calling URL:', `http://localhost:8000/unified-assets/workspace/${workspaceId}`);
      
      const response = await fetch(`http://localhost:8000/unified-assets/workspace/${workspaceId}`);
      
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error(`Workspace not found: ${workspaceId}`);
        } else if (response.status >= 500) {
          throw new Error(`Server error: ${response.status} - Please try again later`);
        } else {
          throw new Error(`API call failed: ${response.status} ${response.statusText}`);
        }
      }
      
      const result: UnifiedAssetsResponse = await response.json();
      
      console.log('🔍 [useUnifiedAssets] Raw response:', result);
      console.log('🔍 [useUnifiedAssets] Received response:', {
        assetCount: result.asset_count,
        totalVersions: result.total_versions,
        dataSource: result.data_source,
        assetKeys: Object.keys(result.assets),
        assetsData: result.assets
      });
      
      setData(result);
      
      console.log('🔍 [useUnifiedAssets] Data set in state. Assets array length:', Object.values(result.assets).length);
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch assets';
      console.error('🔍 [useUnifiedAssets] Error:', errorMessage);
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    console.log('🔍 [useUnifiedAssets] Hook initialized for workspace:', workspaceId);
    fetchAssets();
  }, [fetchAssets]);

  // Convert assets map to array for easy iteration
  const assets = data ? Object.values(data.assets) : [];
  const assetsMap = data ? data.assets : {};

  return {
    assets,
    assetsMap,
    loading,
    error,
    workspaceGoal: data?.workspace_goal || '',
    assetCount: data?.asset_count || 0,
    totalVersions: data?.total_versions || 0,
    refresh: fetchAssets,
  };
};