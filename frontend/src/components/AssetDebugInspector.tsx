'use client';

import React, { useState, useEffect } from 'react';
import { api } from '@/utils/api';

interface AssetDebugInspectorProps {
  workspaceId: string;
}

const AssetDebugInspector: React.FC<AssetDebugInspectorProps> = ({ workspaceId }) => {
  const [debugData, setDebugData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'tasks' | 'deliverables' | 'assets'>('tasks');

  const fetchDebugData = async () => {
    setLoading(true);
    try {
      const [tasksResult, deliverablesResult, assetsResult] = await Promise.allSettled([
        api.monitoring.getWorkspaceTasks(workspaceId, { limit: 10 }),
        api.monitoring.getProjectDeliverables(workspaceId),
        api.assetManagement.getExtractionStatus(workspaceId)
      ]);

      setDebugData({
        tasks: tasksResult.status === 'fulfilled' ? tasksResult.value : null,
        deliverables: deliverablesResult.status === 'fulfilled' ? deliverablesResult.value : null,
        assets: assetsResult.status === 'fulfilled' ? assetsResult.value : null
      });
    } catch (error) {
      console.error('Debug fetch error:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDebugData();
  }, [workspaceId]);

  const renderTaskDetails = (task: any) => {
    const hasDetailedResults = !!task.result?.detailed_results_json;
    let parsedResults = null;
    let hasDualOutput = false;

    if (hasDetailedResults) {
      try {
        parsedResults = typeof task.result.detailed_results_json === 'string' 
          ? JSON.parse(task.result.detailed_results_json)
          : task.result.detailed_results_json;
        hasDualOutput = !!(parsedResults?.structured_content);
      } catch (e) {
        console.log('Parse error:', e);
      }
    }

    return (
      <div key={task.id} className="border rounded-lg p-4 mb-4">
        <div className="flex items-center justify-between mb-2">
          <h4 className="font-medium text-gray-900">{task.name}</h4>
          <div className="flex space-x-2">
            <span className={`px-2 py-1 rounded text-xs ${
              task.status === 'completed' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
            }`}>
              {task.status}
            </span>
            {hasDetailedResults && (
              <span className="px-2 py-1 rounded text-xs bg-blue-100 text-blue-800">
                Has Results
              </span>
            )}
            {hasDualOutput && (
              <span className="px-2 py-1 rounded text-xs bg-purple-100 text-purple-800">
                Dual Output
              </span>
            )}
          </div>
        </div>
        
        <div className="text-sm text-gray-600 mb-2">
          ID: {task.id} | Created: {new Date(task.created_at).toLocaleString()}
        </div>

        {task.context_data && (
          <div className="mb-2">
            <strong className="text-xs text-gray-500">Context Data:</strong>
            <pre className="text-xs bg-gray-100 p-2 rounded mt-1 overflow-auto max-h-20">
              {JSON.stringify(task.context_data, null, 2)}
            </pre>
          </div>
        )}

        {parsedResults && (
          <div className="mb-2">
            <strong className="text-xs text-gray-500">Parsed Results:</strong>
            <div className="text-xs bg-yellow-50 p-2 rounded mt-1">
              <div>Keys: {Object.keys(parsedResults).join(', ')}</div>
              {parsedResults.structured_content && (
                <div className="mt-1">
                  <strong>Structured Content Keys:</strong> {Object.keys(parsedResults.structured_content).join(', ')}
                </div>
              )}
              {parsedResults.rendered_html && (
                <div className="mt-1">
                  <strong>Rendered HTML:</strong> {parsedResults.rendered_html.substring(0, 100)}...
                </div>
              )}
            </div>
          </div>
        )}

        {task.result?.summary && (
          <div className="mb-2">
            <strong className="text-xs text-gray-500">Summary:</strong>
            <p className="text-xs text-gray-700">{task.result.summary.substring(0, 200)}...</p>
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return <div className="p-4">Loading debug data...</div>;
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gray-800 text-white p-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold">🔍 Asset Debug Inspector</h2>
            <button 
              onClick={() => window.location.reload()} 
              className="text-white hover:bg-gray-700 px-3 py-1 rounded"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200">
          <div className="flex">
            {[
              { key: 'tasks', label: '📋 Tasks', count: debugData?.tasks?.length || 0 },
              { key: 'deliverables', label: '📦 Deliverables', count: debugData?.deliverables?.key_outputs?.length || 0 },
              { key: 'assets', label: '🎯 Assets', count: debugData?.assets?.extraction_candidates?.length || 0 }
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key as any)}
                className={`px-4 py-3 border-b-2 transition ${
                  activeTab === tab.key
                    ? 'border-blue-500 text-blue-600 bg-blue-50'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.label} ({tab.count})
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto max-h-[70vh]">
          {activeTab === 'tasks' && (
            <div>
              <h3 className="font-bold mb-4">Recent Tasks</h3>
              {debugData?.tasks?.map ? debugData.tasks.map(renderTaskDetails) : 
               debugData?.tasks?.tasks?.map ? debugData.tasks.tasks.map(renderTaskDetails) :
               <div>No tasks found</div>}
            </div>
          )}

          {activeTab === 'deliverables' && (
            <div>
              <h3 className="font-bold mb-4">Project Deliverables</h3>
              <pre className="text-sm bg-gray-100 p-4 rounded overflow-auto">
                {JSON.stringify(debugData?.deliverables, null, 2)}
              </pre>
            </div>
          )}

          {activeTab === 'assets' && (
            <div>
              <h3 className="font-bold mb-4">Asset Extraction Status</h3>
              <pre className="text-sm bg-gray-100 p-4 rounded overflow-auto">
                {JSON.stringify(debugData?.assets, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 p-4 bg-gray-50">
          <button 
            onClick={fetchDebugData}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            🔄 Refresh Data
          </button>
        </div>
      </div>
    </div>
  );
};

export default AssetDebugInspector;