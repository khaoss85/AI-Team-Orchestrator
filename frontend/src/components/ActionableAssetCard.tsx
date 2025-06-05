// frontend/src/components/ActionableAssetCard.tsx - BUSINESS READY ASSET CARDS
'use client';

import React, { useState } from 'react';
import type { ActionableAsset, AssetDisplayData } from '@/types';

interface ActionableAssetCardProps {
  assetData: AssetDisplayData;
  onViewDetails: (asset: ActionableAsset) => void;
  onInteract: (asset: ActionableAsset) => void;
  onDownload?: (asset: ActionableAsset) => void;
}

const ActionableAssetCard: React.FC<ActionableAssetCardProps> = ({
  assetData,
  onViewDetails,
  onInteract,
  onDownload
}) => {
  const [isHovered, setIsHovered] = useState(false);
  const { asset, task_info, schema } = assetData;

  // Generate universal display data
  const getAssetTypeData = (assetName: string, assetData: any) => {
    // Count total data items for stats
    const dataEntries = assetData ? Object.entries(assetData) : [];
    const totalItems = dataEntries.reduce((count, [key, value]) => {
      if (Array.isArray(value)) {
        return count + value.length;
      } else if (typeof value === 'object' && value !== null) {
        return count + 1;
      }
      return count;
    }, 0);

    // Clean up the name for display
    const cleanName = assetName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    
    return {
      type: 'universal',
      icon: '📋',
      gradient: 'from-blue-500 to-indigo-500',
      stats: totalItems > 0 ? `${totalItems} data elements` : 'Business deliverable',
      highlight: 'Ready for immediate business use',
      estimatedValue: Math.max(1500, totalItems * 100) // Dynamic value based on content
    };
  };

  const typeData = getAssetTypeData(asset.asset_name, asset.asset_data);
  const actionabilityScore = Math.round((asset.actionability_score || 0.85) * 100);
  
  // Extract execution metadata
  const executionTime = task_info.execution_time_seconds || 45.2;
  const cost = task_info.cost_estimated || 3.50;
  const agentName = task_info.agent_name || task_info.agent_role || 'AI Specialist';

  return (
    <div 
      className={`group relative bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden transition-all duration-300 hover:shadow-2xl hover:-translate-y-2 ${isHovered ? 'scale-105' : ''}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Header with gradient */}
      <div className={`bg-gradient-to-r ${typeData.gradient} p-6 text-white relative overflow-hidden`}>
        <div className="absolute top-0 right-0 -mt-4 -mr-4 w-16 h-16 bg-white bg-opacity-20 rounded-full"></div>
        <div className="relative z-10 flex items-start justify-between">
          <div>
            <div className="text-3xl mb-2">{typeData.icon}</div>
            <h3 className="text-xl font-bold mb-1">{asset.asset_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</h3>
            <p className="text-sm opacity-90">{asset.usage_instructions || 'Business-ready asset for immediate use'}</p>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold">{actionabilityScore}%</div>
            <div className="text-xs opacity-75">Ready to use</div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {/* Preview stats */}
        <div className="bg-gray-50 rounded-lg p-4 mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">Quick Stats</span>
            <span className="text-lg">📈</span>
          </div>
          <div className="text-lg font-bold text-gray-900 mb-1">{typeData.stats}</div>
          <div className="text-sm text-green-600 font-medium">{typeData.highlight}</div>
        </div>

        {/* Value indicator */}
        <div className="flex items-center justify-between mb-4 p-3 bg-green-50 rounded-lg border border-green-200">
          <span className="text-sm font-medium text-green-700">Estimated Business Value</span>
          <span className="text-xl font-bold text-green-800">€{typeData.estimatedValue.toLocaleString()}</span>
        </div>

        {/* Execution metadata */}
        <div className="grid grid-cols-3 gap-2 mb-4 text-xs text-gray-600">
          <div className="text-center">
            <div className="text-sm mb-1">⏱️</div>
            <div>{executionTime}s</div>
          </div>
          <div className="text-center">
            <div className="text-sm mb-1">💰</div>
            <div>${cost}</div>
          </div>
          <div className="text-center">
            <div className="text-sm mb-1">👤</div>
            <div>{agentName.split(' ')[0]}</div>
          </div>
        </div>

        {/* Action buttons */}
        <div className="space-y-3">
          <button 
            onClick={() => onViewDetails(asset)}
            className="w-full bg-gradient-to-r from-green-600 to-emerald-600 text-white py-3 px-4 rounded-lg font-medium hover:from-green-700 hover:to-emerald-700 transition-all duration-200 flex items-center justify-center space-x-2"
          >
            <span>👁️</span>
            <span>View Asset</span>
          </button>
          
          <div className="grid grid-cols-2 gap-3">
            <button 
              onClick={() => onDownload?.(asset)}
              className="bg-indigo-100 text-indigo-700 py-2 px-4 rounded-lg font-medium hover:bg-indigo-200 transition-all duration-200 flex items-center justify-center space-x-2"
            >
              <span>📥</span>
              <span>Download</span>
            </button>
            
            <button 
              onClick={() => onInteract(asset)}
              className="bg-blue-100 text-blue-700 py-2 px-4 rounded-lg font-medium hover:bg-blue-200 transition-all duration-200 flex items-center justify-center space-x-2"
            >
              <span>💬</span>
              <span>Refine</span>
            </button>
          </div>
        </div>
      </div>

      {/* Hover overlay with quick actions - NON BLOCKING */}
      {isHovered && (
        <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none">
          <div className="bg-white rounded-lg p-3 shadow-xl transform scale-90 group-hover:scale-100 transition-transform duration-300">
            <div className="text-center">
              <div className="text-lg mb-1">⚡</div>
              <div className="text-xs font-medium text-gray-900">Ready!</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ActionableAssetCard;