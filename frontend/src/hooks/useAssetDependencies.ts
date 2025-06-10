'use client';

import { useState, useCallback } from 'react';
import { api } from '@/utils/api';

// Interfacce flessibili per sistema multi-disciplinare
export interface AssetDependency {
  id: string;
  name: string;
  type: string; // "competitor_analysis", "content_strategy", "financial_model", etc.
  impact_level: 'low' | 'medium' | 'high' | 'critical';
  update_reason: string;
  auto_applicable: boolean;
  estimated_effort: 'quick' | 'moderate' | 'extensive';
  category: string; // "marketing", "finance", "product", "research", etc.
  last_updated: string;
  quality_score?: number;
  business_value?: number;
}

export interface AssetUpdateSuggestion {
  source_asset: {
    id: string;
    name: string;
    type: string;
    version: string;
  };
  affected_assets: AssetDependency[];
  update_rationale: string;
  batch_update_possible: boolean;
  estimated_total_time: string;
  business_impact_summary: string;
}

export interface AssetVersion {
  version: string;
  created_at: string;
  created_by: string;
  changes_summary: string;
  quality_metrics: {
    actionability: number;
    completeness: number;
    accuracy: number;
    business_relevance: number;
  };
  size_indicators: {
    word_count?: number;
    data_points?: number;
    sections?: number;
  };
  content_preview: string;
}

export interface AssetHistory {
  asset_id: string;
  asset_name: string;
  asset_type: string;
  current_version: string;
  versions: AssetVersion[];
  total_iterations: number;
  first_created: string;
  last_modified: string;
}

interface UseAssetDependenciesReturn {
  // State
  suggestions: AssetUpdateSuggestion | null;
  history: AssetHistory | null;
  loading: boolean;
  error: string | null;
  
  // Actions
  checkDependencies: (assetId: string) => Promise<AssetUpdateSuggestion | null>;
  applySelectedUpdates: (assetId: string, selectedIds: string[], options?: UpdateOptions) => Promise<void>;
  fetchAssetHistory: (assetId: string) => Promise<AssetHistory | null>;
  compareVersions: (assetId: string, fromVersion: string, toVersion: string) => Promise<any>;
  
  // Utility
  clearSuggestions: () => void;
  clearHistory: () => void;
}

interface UpdateOptions {
  priority?: 'low' | 'medium' | 'high';
  batch_mode?: boolean;
  notify_completion?: boolean;
  preserve_manual_changes?: boolean;
}

export const useAssetDependencies = (): UseAssetDependenciesReturn => {
  const [suggestions, setSuggestions] = useState<AssetUpdateSuggestion | null>(null);
  const [history, setHistory] = useState<AssetHistory | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const checkDependencies = useCallback(async (assetId: string): Promise<AssetUpdateSuggestion | null> => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await api.assets.checkDependencies(assetId);
      setSuggestions(response);
      return response;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to check dependencies');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const applySelectedUpdates = useCallback(async (
    assetId: string, 
    selectedIds: string[], 
    options: UpdateOptions = {}
  ): Promise<void> => {
    try {
      setLoading(true);
      setError(null);
      
      await api.assets.applyDependencyUpdates(assetId, {
        selected_asset_ids: selectedIds,
        options: {
          priority: options.priority || 'medium',
          batch_mode: options.batch_mode || false,
          notify_completion: options.notify_completion !== false,
          preserve_manual_changes: options.preserve_manual_changes !== false
        }
      });
      
      // Clear suggestions after successful update
      setSuggestions(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to apply updates');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchAssetHistory = useCallback(async (assetId: string): Promise<AssetHistory | null> => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await api.assets.getHistory(assetId);
      setHistory(response);
      return response;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch asset history');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const compareVersions = useCallback(async (
    assetId: string, 
    fromVersion: string, 
    toVersion: string
  ) => {
    try {
      setLoading(true);
      setError(null);
      
      return await api.assets.compareVersions(assetId, fromVersion, toVersion);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to compare versions');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const clearSuggestions = useCallback(() => {
    setSuggestions(null);
  }, []);

  const clearHistory = useCallback(() => {
    setHistory(null);
  }, []);

  return {
    suggestions,
    history,
    loading,
    error,
    checkDependencies,
    applySelectedUpdates,
    fetchAssetHistory,
    compareVersions,
    clearSuggestions,
    clearHistory
  };
};