'use client';

import React, { useState } from 'react';
import { createPortal } from 'react-dom';
import { AssetDependency, AssetUpdateSuggestion } from '@/hooks/useAssetDependencies';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  suggestion: AssetUpdateSuggestion;
  onApplyUpdates: (selectedIds: string[], options: UpdateOptions) => Promise<void>;
  loading?: boolean;
}

interface UpdateOptions {
  priority: 'low' | 'medium' | 'high';
  batch_mode: boolean;
  notify_completion: boolean;
  preserve_manual_changes: boolean;
}

// Configurazione flessibile per icone e colori per diversi domini
const DOMAIN_CONFIG = {
  marketing: { icon: '📱', color: 'blue', label: 'Marketing' },
  finance: { icon: '💰', color: 'green', label: 'Finance' },
  product: { icon: '🚀', color: 'purple', label: 'Product' },
  research: { icon: '🔬', color: 'yellow', label: 'Research' },
  operations: { icon: '⚙️', color: 'gray', label: 'Operations' },
  strategy: { icon: '🎯', color: 'indigo', label: 'Strategy' },
  content: { icon: '📝', color: 'orange', label: 'Content' },
  design: { icon: '🎨', color: 'pink', label: 'Design' },
  technology: { icon: '💻', color: 'cyan', label: 'Technology' },
  legal: { icon: '⚖️', color: 'red', label: 'Legal' },
  hr: { icon: '👥', color: 'emerald', label: 'Human Resources' },
  default: { icon: '📊', color: 'slate', label: 'General' }
};

const IMPACT_CONFIG = {
  critical: { icon: '🔥', color: 'red', label: 'Critical', description: 'Major business impact' },
  high: { icon: '⚡', color: 'orange', label: 'High', description: 'Significant improvements' },
  medium: { icon: '📈', color: 'yellow', label: 'Medium', description: 'Moderate enhancements' },
  low: { icon: '🔧', color: 'green', label: 'Low', description: 'Minor optimizations' }
};

const EFFORT_CONFIG = {
  quick: { icon: '⚡', time: '< 5 min', color: 'green' },
  moderate: { icon: '🔄', time: '5-15 min', color: 'yellow' },
  extensive: { icon: '⏳', time: '15+ min', color: 'red' }
};

export const RelatedAssetsModal: React.FC<Props> = ({
  isOpen,
  onClose,
  suggestion,
  onApplyUpdates,
  loading = false
}) => {
  const [selectedAssets, setSelectedAssets] = useState<Set<string>>(new Set());
  const [updateOptions, setUpdateOptions] = useState<UpdateOptions>({
    priority: 'medium',
    batch_mode: true,
    notify_completion: true,
    preserve_manual_changes: true
  });
  const [applying, setApplying] = useState(false);

  if (!isOpen) return null;

  const handleAssetToggle = (assetId: string) => {
    const newSelected = new Set(selectedAssets);
    if (newSelected.has(assetId)) {
      newSelected.delete(assetId);
    } else {
      newSelected.add(assetId);
    }
    setSelectedAssets(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedAssets.size === suggestion.affected_assets.length) {
      setSelectedAssets(new Set());
    } else {
      setSelectedAssets(new Set(suggestion.affected_assets.map(a => a.id)));
    }
  };

  const handleApply = async () => {
    try {
      setApplying(true);
      await onApplyUpdates(Array.from(selectedAssets), updateOptions);
      onClose();
    } catch (error) {
      console.error('Failed to apply updates:', error);
    } finally {
      setApplying(false);
    }
  };

  const getDomainConfig = (category: string) => {
    return DOMAIN_CONFIG[category.toLowerCase() as keyof typeof DOMAIN_CONFIG] || DOMAIN_CONFIG.default;
  };

  const getImpactConfig = (level: string) => {
    return IMPACT_CONFIG[level as keyof typeof IMPACT_CONFIG] || IMPACT_CONFIG.medium;
  };

  const getEffortConfig = (effort: string) => {
    return EFFORT_CONFIG[effort as keyof typeof EFFORT_CONFIG] || EFFORT_CONFIG.moderate;
  };

  const canApply = selectedAssets.size > 0 && !applying && !loading;
  const allSelected = selectedAssets.size === suggestion.affected_assets.length;

  return createPortal(
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 px-6 py-4 border-b border-blue-200">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-blue-900">Asset Update Suggestions</h2>
              <p className="text-sm text-blue-700 mt-1">
                {suggestion.source_asset.name} has been updated. Related assets may benefit from updates.
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-blue-400 hover:text-blue-600 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex flex-col h-full max-h-[calc(90vh-80px)]">
          {/* Summary */}
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
              <div className="flex items-start">
                <div className="text-amber-600 mr-3 mt-0.5">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="flex-1">
                  <h3 className="text-sm font-medium text-amber-800">Update Impact Analysis</h3>
                  <p className="text-sm text-amber-700 mt-1">{suggestion.update_rationale}</p>
                  <div className="mt-2 text-xs text-amber-600">
                    <strong>Business Impact:</strong> {suggestion.business_impact_summary}
                  </div>
                  {suggestion.batch_update_possible && (
                    <div className="mt-1 text-xs text-amber-600">
                      ⚡ Batch update available - estimated time: {suggestion.estimated_total_time}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Asset List */}
          <div className="flex-1 overflow-auto px-6 py-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                Affected Assets ({suggestion.affected_assets.length})
              </h3>
              <button
                onClick={handleSelectAll}
                className="text-sm text-blue-600 hover:text-blue-800 font-medium"
              >
                {allSelected ? 'Deselect All' : 'Select All'}
              </button>
            </div>

            <div className="space-y-3">
              {suggestion.affected_assets.map((asset) => {
                const domainConfig = getDomainConfig(asset.category);
                const impactConfig = getImpactConfig(asset.impact_level);
                const effortConfig = getEffortConfig(asset.estimated_effort);
                const isSelected = selectedAssets.has(asset.id);

                return (
                  <div
                    key={asset.id}
                    className={`border rounded-lg p-4 cursor-pointer transition-all ${
                      isSelected 
                        ? 'border-blue-300 bg-blue-50 shadow-sm' 
                        : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'
                    }`}
                    onClick={() => handleAssetToggle(asset.id)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-3 flex-1">
                        <div className="flex-shrink-0 mt-1">
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => handleAssetToggle(asset.id)}
                            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                            onClick={(e) => e.stopPropagation()}
                          />
                        </div>
                        
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <span className="text-lg">{domainConfig.icon}</span>
                            <h4 className="font-medium text-gray-900">{asset.name}</h4>
                            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-${domainConfig.color}-100 text-${domainConfig.color}-800`}>
                              {domainConfig.label}
                            </span>
                          </div>
                          
                          <p className="text-sm text-gray-600 mb-3">{asset.update_reason}</p>
                          
                          <div className="flex items-center space-x-4 text-xs">
                            <div className={`flex items-center space-x-1 text-${impactConfig.color}-600`}>
                              <span>{impactConfig.icon}</span>
                              <span className="font-medium">{impactConfig.label} Impact</span>
                            </div>
                            
                            <div className={`flex items-center space-x-1 text-${effortConfig.color}-600`}>
                              <span>{effortConfig.icon}</span>
                              <span>{effortConfig.time}</span>
                            </div>
                            
                            {asset.auto_applicable && (
                              <div className="flex items-center space-x-1 text-green-600">
                                <span>🤖</span>
                                <span>Auto-applicable</span>
                              </div>
                            )}
                            
                            {asset.quality_score && (
                              <div className="flex items-center space-x-1 text-gray-600">
                                <span>📊</span>
                                <span>Quality: {Math.round(asset.quality_score * 100)}%</span>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Options */}
          <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
            <h4 className="text-sm font-medium text-gray-900 mb-3">Update Options</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Priority</label>
                <select
                  value={updateOptions.priority}
                  onChange={(e) => setUpdateOptions({...updateOptions, priority: e.target.value as any})}
                  className="w-full text-xs border border-gray-300 rounded px-2 py-1"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
              
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="batch_mode"
                  checked={updateOptions.batch_mode}
                  onChange={(e) => setUpdateOptions({...updateOptions, batch_mode: e.target.checked})}
                  className="mr-2"
                />
                <label htmlFor="batch_mode" className="text-xs text-gray-700">Batch Mode</label>
              </div>
              
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="notify"
                  checked={updateOptions.notify_completion}
                  onChange={(e) => setUpdateOptions({...updateOptions, notify_completion: e.target.checked})}
                  className="mr-2"
                />
                <label htmlFor="notify" className="text-xs text-gray-700">Notify on Completion</label>
              </div>
              
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="preserve"
                  checked={updateOptions.preserve_manual_changes}
                  onChange={(e) => setUpdateOptions({...updateOptions, preserve_manual_changes: e.target.checked})}
                  className="mr-2"
                />
                <label htmlFor="preserve" className="text-xs text-gray-700">Preserve Manual Changes</label>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="px-6 py-4 border-t border-gray-200 bg-white">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-600">
                {selectedAssets.size} of {suggestion.affected_assets.length} assets selected
              </div>
              
              <div className="flex space-x-3">
                <button
                  onClick={onClose}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                  disabled={applying}
                >
                  Skip for Now
                </button>
                
                <button
                  onClick={handleApply}
                  disabled={!canApply}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
                >
                  {applying && (
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                  )}
                  <span>
                    {applying ? 'Applying Updates...' : `Update Selected (${selectedAssets.size})`}
                  </span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
};