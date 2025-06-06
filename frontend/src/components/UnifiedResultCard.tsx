// frontend/src/components/UnifiedResultCard.tsx - UNIFIED RESULT CARD COMPONENT

'use client';

import React, { useState } from 'react';
import { UnifiedResultItem } from '@/hooks/useProjectResults';

interface UnifiedResultCardProps {
  result: UnifiedResultItem;
  onViewDetails?: (result: UnifiedResultItem) => void;
  onDownload?: (result: UnifiedResultItem) => void;
  onUse?: (result: UnifiedResultItem) => void;
  onShare?: (result: UnifiedResultItem) => void;
  showActions?: boolean;
  compact?: boolean;
  isSelected?: boolean;
  onToggleSelection?: (id: string) => void;
  onExport?: (result: UnifiedResultItem, format: 'json' | 'txt' | 'md') => void;
}

export const UnifiedResultCard: React.FC<UnifiedResultCardProps> = ({
  result,
  onViewDetails,
  isSelected = false,
  onToggleSelection,
  onExport,
  onDownload,
  onUse,
  onShare,
  showActions = true,
  compact = false
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showExportMenu, setShowExportMenu] = useState(false);

  // Icon mapping based on type and category
  const getResultIcon = () => {
    if (result.type === 'asset') {
      if (result.category === 'content') return '📅';
      if (result.category === 'data') return '📊';
      if (result.category === 'strategy') return '🎯';
      return '📄';
    }
    
    if (result.type === 'deliverable') {
      if (result.businessImpact === 'critical') return '🎯';
      if (result.category === 'analysis') return '📈';
      if (result.category === 'strategy') return '🎯';
      return '📋';
    }
    
    return '💼';
  };

  // Color scheme based on business impact and readiness
  const getCardColors = () => {
    if (!result.readyToUse) {
      return 'border-gray-200 bg-gray-50 hover:bg-gray-100';
    }
    
    switch (result.businessImpact) {
      case 'critical':
        return 'border-red-200 bg-red-50 hover:bg-red-100';
      case 'high':
        return 'border-green-200 bg-green-50 hover:bg-green-100';
      case 'medium':
        return 'border-blue-200 bg-blue-50 hover:bg-blue-100';
      case 'low':
        return 'border-yellow-200 bg-yellow-50 hover:bg-yellow-100';
      default:
        return 'border-gray-200 bg-white hover:bg-gray-50';
    }
  };

  // Badge color for business impact
  const getBadgeColors = () => {
    switch (result.businessImpact) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'high':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'medium':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'low':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  // Render key insights
  const renderKeyInsights = () => {
    if (!result.keyInsights?.length) return null;
    
    const insights = isExpanded ? result.keyInsights : result.keyInsights.slice(0, 2);
    
    return (
      <div className="mt-3">
        <h4 className="text-sm font-medium text-gray-700 mb-2">💡 Insights Chiave</h4>
        <ul className="space-y-1">
          {insights.map((insight, index) => (
            <li key={index} className="flex items-start text-sm text-gray-600">
              <span className="w-1 h-1 bg-gray-400 rounded-full mt-2 mr-2 flex-shrink-0"></span>
              <span>{insight}</span>
            </li>
          ))}
        </ul>
        {result.keyInsights.length > 2 && !isExpanded && (
          <button
            onClick={() => setIsExpanded(true)}
            className="text-xs text-blue-600 hover:text-blue-800 mt-1"
          >
            +{result.keyInsights.length - 2} altri insights
          </button>
        )}
      </div>
    );
  };

  // Render metrics
  const renderMetrics = () => {
    if (!result.metrics || Object.keys(result.metrics).length === 0) return null;
    
    const metricsEntries = Object.entries(result.metrics).slice(0, 3);
    
    return (
      <div className="mt-3">
        <h4 className="text-sm font-medium text-gray-700 mb-2">📊 Metriche</h4>
        <div className="grid grid-cols-2 gap-2">
          {metricsEntries.map(([key, value]) => (
            <div key={key} className="text-xs">
              <span className="text-gray-500 capitalize">{key.replace(/_/g, ' ')}</span>
              <div className="font-semibold text-gray-800">
                {typeof value === 'number' ? value.toLocaleString() : String(value)}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className={`rounded-lg border shadow-sm transition-all duration-200 ${getCardColors()}`}>
      <div className={compact ? "p-4" : "p-6"}>
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center space-x-3">
            {/* Selection checkbox */}
            {onToggleSelection && (
              <input
                type="checkbox"
                checked={isSelected}
                onChange={() => onToggleSelection(result.id)}
                className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
              />
            )}
            
            <div className="text-2xl">{getResultIcon()}</div>
            <div className="min-w-0 flex-1">
              <h3 className={`font-semibold text-gray-900 ${compact ? 'text-base' : 'text-lg'}`}>
                {result.title}
              </h3>
              <p className="text-sm text-gray-500">
                {result.agentName} • {result.agentRole}
              </p>
            </div>
          </div>
          
          {/* Status badges */}
          <div className="flex flex-col space-y-1">
            {result.readyToUse && (
              <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full font-medium">
                ✅ Pronto
              </span>
            )}
            <span className={`text-xs px-2 py-1 rounded-full font-medium border ${getBadgeColors()}`}>
              {result.businessImpact === 'critical' ? 'Critico' :
               result.businessImpact === 'high' ? 'Alto Impatto' :
               result.businessImpact === 'medium' ? 'Medio' : 'Basso'}
            </span>
          </div>
        </div>

        {/* Description */}
        <p className="text-sm text-gray-600 mb-4 leading-relaxed">
          {result.description}
        </p>

        {/* Quality indicators */}
        <div className="flex space-x-4 mb-4">
          <div className="flex-1">
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="text-gray-600">Azionabilità</span>
              <span className="font-medium">{Math.round(result.actionabilityScore * 100)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-1.5">
              <div 
                className={`h-1.5 rounded-full transition-all duration-300 ${
                  result.actionabilityScore >= 0.8 ? 'bg-green-500' :
                  result.actionabilityScore >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                style={{ width: `${result.actionabilityScore * 100}%` }}
              />
            </div>
          </div>
          
          <div className="flex-1">
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="text-gray-600">Validazione</span>
              <span className="font-medium">{Math.round(result.validationScore * 100)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-1.5">
              <div 
                className={`h-1.5 rounded-full transition-all duration-300 ${
                  result.validationScore >= 0.8 ? 'bg-green-500' :
                  result.validationScore >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                style={{ width: `${result.validationScore * 100}%` }}
              />
            </div>
          </div>
        </div>

        {/* Usage instructions */}
        {result.usageInstructions && (
          <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
            <h4 className="font-medium text-blue-800 text-sm mb-1">💡 Come utilizzare</h4>
            <p className="text-sm text-blue-700">{result.usageInstructions}</p>
          </div>
        )}

        {/* Key insights */}
        {!compact && renderKeyInsights()}

        {/* Metrics */}
        {!compact && renderMetrics()}

        {/* Visual summary */}
        {result.visualSummary && !compact && (
          <div className="mt-3 p-3 bg-gray-50 rounded-lg">
            <h4 className="text-sm font-medium text-gray-700 mb-1">👁️ Riepilogo Visivo</h4>
            <p className="text-sm text-gray-600">{result.visualSummary}</p>
          </div>
        )}

        {/* Actions */}
        {showActions && (
          <div className="mt-4 flex flex-wrap gap-2">
            {result.actions.canView && onViewDetails && (
              <button
                onClick={() => onViewDetails(result)}
                className="flex-1 min-w-[120px] px-3 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition flex items-center justify-center"
              >
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                Visualizza
              </button>
            )}

            {result.actions.canDownload && onDownload && (
              <button
                onClick={() => onDownload(result)}
                className="flex-1 min-w-[120px] px-3 py-2 bg-green-600 text-white rounded-md text-sm hover:bg-green-700 transition flex items-center justify-center"
              >
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Scarica
              </button>
            )}

            {result.actions.canUse && result.readyToUse && onUse && (
              <button
                onClick={() => onUse(result)}
                className="flex-1 min-w-[120px] px-3 py-2 bg-purple-600 text-white rounded-md text-sm hover:bg-purple-700 transition flex items-center justify-center"
              >
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Usa Ora
              </button>
            )}

            {/* Export menu */}
            {onExport && (
              <div className="relative">
                <button
                  onClick={() => setShowExportMenu(!showExportMenu)}
                  className="px-3 py-2 bg-gray-100 text-gray-700 rounded-md text-sm hover:bg-gray-200 transition flex items-center"
                  title="Esporta contenuto"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </button>
                
                {showExportMenu && (
                  <div className="absolute right-0 mt-2 w-32 bg-white rounded-md shadow-lg z-10 border">
                    <div className="py-1">
                      <button
                        onClick={() => {
                          onExport(result, 'json');
                          setShowExportMenu(false);
                        }}
                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        Export JSON
                      </button>
                      <button
                        onClick={() => {
                          onExport(result, 'md');
                          setShowExportMenu(false);
                        }}
                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        Export Markdown
                      </button>
                      <button
                        onClick={() => {
                          onExport(result, 'txt');
                          setShowExportMenu(false);
                        }}
                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        Export Text
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}

            {result.actions.canShare && onShare && (
              <button
                onClick={() => onShare(result)}
                className="px-3 py-2 bg-gray-100 text-gray-700 rounded-md text-sm hover:bg-gray-200 transition flex items-center"
              >
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.367 2.684 3 3 0 00-5.367-2.684z" />
                </svg>
                Condividi
              </button>
            )}

            {/* Copy to clipboard button */}
            <button
              onClick={() => {
                const contentStr = result.structuredContent ? 
                  JSON.stringify(result.structuredContent, null, 2) : 
                  result.description;
                navigator.clipboard.writeText(contentStr);
                // Could add toast notification here
              }}
              className="px-3 py-2 bg-gray-100 text-gray-700 rounded-md text-sm hover:bg-gray-200 transition flex items-center"
              title="Copia negli appunti"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            </button>
          </div>
        )}

        {/* Footer metadata */}
        <div className="mt-4 pt-3 border-t border-gray-200 flex justify-between text-xs text-gray-500">
          <div>
            <span>Task: {result.sourceTaskId.substring(0, 8)}...</span>
            {result.automationReady && (
              <span className="ml-2 bg-blue-100 text-blue-700 px-1 rounded">🤖 Auto</span>
            )}
          </div>
          <div>
            {new Date(result.lastUpdated).toLocaleDateString('it-IT')}
          </div>
        </div>
      </div>
    </div>
  );
};

export default UnifiedResultCard;