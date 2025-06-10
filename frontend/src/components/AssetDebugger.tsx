'use client';

import React, { useState, useEffect } from 'react';

interface AssetDebuggerProps {
  workspaceId: string;
  tasks: any[];
  assets: any;
  loading: boolean;
  processedAssets?: any[];
  assetDisplayData?: any[];
}

const AssetDebugger: React.FC<AssetDebuggerProps> = ({ workspaceId, tasks, assets, loading, processedAssets, assetDisplayData }) => {
  const [expanded, setExpanded] = useState(false);
  const [debugInfo, setDebugInfo] = useState<any>(null);

  useEffect(() => {
    const checkAssetAvailability = () => {
      // Debug info
      const info = {
        workspaceId,
        totalTasks: tasks.length,
        totalAssets: Object.keys(assets).length,
        tasksWithResults: tasks.filter(t => t.result).length,
        tasksCompleted: tasks.filter(t => t.status === 'completed').length,
        taskNames: tasks.map(t => t.name).slice(0, 10), // First 10 task names
        assetSources: Object.entries(assets).map(([key, asset]: [string, any]) => ({
          key,
          assetName: asset.asset_name,
          sourceTaskId: asset.source_task_id,
          taskName: tasks.find(t => t.id === asset.source_task_id)?.name
        })),
        processedAssetsCount: processedAssets?.length || 0,
        assetDisplayDataCount: assetDisplayData?.length || 0,
        allTasksWithDetailedResults: tasks.filter(t => t.result?.detailed_results_json).length,
        competitorRelatedTasks: tasks.filter(t => 
          t.name?.toLowerCase().includes('competitor') || 
          t.name?.toLowerCase().includes('competition') ||
          t.result?.summary?.toLowerCase().includes('competitor') ||
          t.result?.summary?.toLowerCase().includes('competition')
        ).map(t => t.name)
      };
      setDebugInfo(info);
    };

    if (!loading && tasks.length >= 0) {
      checkAssetAvailability();
    }
  }, [workspaceId, tasks, assets, loading]);

  if (!debugInfo) return null;

  return (
    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
      <button 
        onClick={() => setExpanded(!expanded)}
        className="flex items-center w-full text-left text-sm font-medium text-yellow-800"
      >
        <span className="mr-2">🔍</span>
        Debug Info: Asset Loading Analysis
        <span className="ml-auto">{expanded ? '▼' : '▶'}</span>
      </button>
      
      {expanded && (
        <div className="mt-4 text-sm text-yellow-700 space-y-2">
          <div><strong>Workspace ID:</strong> {debugInfo.workspaceId}</div>
          <div><strong>Total Tasks Found:</strong> {debugInfo.totalTasks}</div>
          <div><strong>Tasks with Results:</strong> {debugInfo.tasksWithResults}</div>
          <div><strong>Completed Tasks:</strong> {debugInfo.tasksCompleted}</div>
          <div><strong>Tasks with Detailed Results:</strong> {debugInfo.allTasksWithDetailedResults}</div>
          <div><strong>Total Assets Extracted:</strong> {debugInfo.totalAssets}</div>
          <div><strong>Processed Assets Count:</strong> {debugInfo.processedAssetsCount}</div>
          <div><strong>Asset Display Data Count:</strong> {debugInfo.assetDisplayDataCount}</div>
          
          {debugInfo.competitorRelatedTasks && debugInfo.competitorRelatedTasks.length > 0 && (
            <div>
              <strong>Competitor-related Tasks Found:</strong>
              <ul className="ml-4 mt-1">
                {debugInfo.competitorRelatedTasks.map((name: string, i: number) => (
                  <li key={i} className="text-xs text-green-700">• {name}</li>
                ))}
              </ul>
            </div>
          )}
          
          {debugInfo.taskNames.length > 0 && (
            <div>
              <strong>Recent Task Names:</strong>
              <ul className="ml-4 mt-1">
                {debugInfo.taskNames.map((name: string, i: number) => (
                  <li key={i} className="text-xs">• {name}</li>
                ))}
              </ul>
            </div>
          )}
          
          {debugInfo.assetSources.length > 0 && (
            <div>
              <strong>Asset Sources:</strong>
              <ul className="ml-4 mt-1">
                {debugInfo.assetSources.map((source: any, i: number) => (
                  <li key={i} className="text-xs">
                    • {source.assetName} (from task: {source.taskName})
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {debugInfo.totalTasks === 0 && (
            <div className="bg-red-100 border border-red-300 rounded p-3 mt-3">
              <strong className="text-red-800">⚠️ Issue Found:</strong>
              <p className="text-red-700 text-xs mt-1">
                No tasks found in this workspace. This could mean:
                <br/>• You're viewing an empty or new workspace
                <br/>• Tasks haven't been created yet
                <br/>• There's an API issue loading tasks
              </p>
            </div>
          )}
          
          {debugInfo.totalTasks > 0 && debugInfo.totalAssets === 0 && (
            <div className="bg-orange-100 border border-orange-300 rounded p-3 mt-3">
              <strong className="text-orange-800">⚠️ Issue Found:</strong>
              <p className="text-orange-700 text-xs mt-1">
                Tasks exist but no assets were extracted. This could mean:
                <br/>• Tasks don't have results yet
                <br/>• Asset extraction logic needs refinement
                <br/>• Results don't match expected format
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AssetDebugger;