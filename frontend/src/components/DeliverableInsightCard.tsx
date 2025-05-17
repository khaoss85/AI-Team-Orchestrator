import React from 'react';
import { ProjectDeliverableCard } from '@/types';

interface DeliverableInsightCardProps {
  card: ProjectDeliverableCard;
  onViewDetails?: () => void;
}

export default function DeliverableInsightCard({ card, onViewDetails }: DeliverableInsightCardProps) {
  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'research': return {
        bg: 'from-blue-500 to-blue-600',
        iconBg: 'bg-blue-400 bg-opacity-30',
        border: 'border-blue-400'
      };
      case 'planning': return {
        bg: 'from-purple-500 to-purple-600',
        iconBg: 'bg-purple-400 bg-opacity-30',
        border: 'border-purple-400'
      };
      case 'execution': return {
        bg: 'from-green-500 to-green-600',
        iconBg: 'bg-green-400 bg-opacity-30',
        border: 'border-green-400'
      };
      case 'analysis': return {
        bg: 'from-orange-500 to-orange-600',
        iconBg: 'bg-orange-400 bg-opacity-30',
        border: 'border-orange-400'
      };
      case 'review': return {
        bg: 'from-red-500 to-red-600',
        iconBg: 'bg-red-400 bg-opacity-30',
        border: 'border-red-400'
      };
      default: return {
        bg: 'from-gray-600 to-gray-700',
        iconBg: 'bg-gray-500 bg-opacity-30',
        border: 'border-gray-400'
      };
    }
  };

  const colors = getCategoryColor(card.category);
  
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('it-IT', {
      day: 'numeric',
      month: 'short'
    });
  };

  const renderMetrics = () => {
    if (!card.metrics) return null;

    return (
      <div className="mt-3 flex flex-wrap gap-2">
        {Object.entries(card.metrics).map(([key, values]) => (
          <div key={key} className="text-xs">
            {Array.isArray(values) ? (
              values.map((value, idx) => (
                <span key={idx} className="inline-block bg-white bg-opacity-20 rounded-full px-2 py-1 mr-1 mb-1">
                  {value}
                </span>
              ))
            ) : (
              <span className="inline-block bg-white bg-opacity-20 rounded-full px-2 py-1">
                {values}
              </span>
            )}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className={`relative overflow-hidden rounded-xl bg-gradient-to-br ${colors.bg} p-6 text-white shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className={`w-10 h-10 flex items-center justify-center rounded-lg ${colors.iconBg} ${colors.border}`}>
            <span className="text-2xl">{card.icon}</span>
          </div>
          <div>
            <h3 className="text-lg font-semibold">{card.title}</h3>
            <p className="text-sm opacity-90">{card.category}</p>
          </div>
        </div>
        <div className="text-right text-xs opacity-75">
          <div>{formatDate(card.created_at)}</div>
          <div>da {card.created_by}</div>
        </div>
      </div>

      {/* Description */}
      <div className="mb-4">
        <p className="text-sm leading-relaxed opacity-95">
          {card.description}
        </p>
      </div>

      {/* Key Insights */}
      {card.key_insights.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-medium mb-2 opacity-90">Insight chiave:</h4>
          <ul className="space-y-1">
            {card.key_insights.slice(0, 3).map((insight, index) => (
              <li key={index} className="text-xs flex items-start">
                <span className="mt-1 mr-2 opacity-75">•</span>
                <span className="opacity-95">{insight}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Metrics */}
      {renderMetrics()}

      {/* Completeness Score */}
      <div className="mt-4 pt-4 border-t border-white border-opacity-20">
        <div className="flex items-center justify-between">
          <span className="text-xs opacity-75">Completezza</span>
          <span className="text-sm font-medium">{card.completeness_score}%</span>
        </div>
        <div className="mt-1 w-full bg-white bg-opacity-20 rounded-full h-2">
          <div 
            className="bg-white h-2 rounded-full transition-all duration-500"
            style={{ width: `${card.completeness_score}%` }}
          ></div>
        </div>
      </div>

      {/* View Details Button */}
      {onViewDetails && (
        <button
          onClick={onViewDetails}
          className="absolute bottom-4 right-4 bg-white bg-opacity-20 hover:bg-opacity-30 rounded-full p-2 transition-all duration-200"
          aria-label="View details"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      )}

      {/* Decorative elements */}
      <div className="absolute top-0 right-0 -mt-4 -mr-4 w-16 h-16 bg-white bg-opacity-10 rounded-full"></div>
      <div className="absolute bottom-0 left-0 -mb-4 -ml-4 w-12 h-12 bg-white bg-opacity-10 rounded-full"></div>
    </div>
  );
}