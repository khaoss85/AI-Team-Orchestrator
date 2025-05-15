'use client';

import React from 'react';
import { ProjectDeliverableCard } from '@/types';

interface DeliverableInsightCardProps {
  card: ProjectDeliverableCard;
  onViewDetails?: () => void;
}

export default function DeliverableInsightCard({ card, onViewDetails }: DeliverableInsightCardProps) {
  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'research': return 'from-blue-500 to-blue-600';
      case 'planning': return 'from-purple-500 to-purple-600';
      case 'execution': return 'from-green-500 to-green-600';
      case 'analysis': return 'from-orange-500 to-orange-600';
      case 'review': return 'from-red-500 to-red-600';
      default: return 'from-gray-500 to-gray-600';
    }
  };

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
                <span key={idx} className="inline-block bg-white bg-opacity-20 rounded-full px-2 py-1 mr-1">
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
    <div className={`relative overflow-hidden rounded-xl bg-gradient-to-br ${getCategoryColor(card.category)} p-6 text-white shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <span className="text-3xl">{card.icon}</span>
          <div>
            <h3 className="text-lg font-semibold">{card.title}</h3>
            <p className="text-sm opacity-90">{card.category}</p>
          </div>
        </div>
        <div className="text-right">
          <div className="text-xs opacity-75">{formatDate(card.created_at)}</div>
          <div className="text-xs opacity-75">by {card.created_by}</div>
        </div>
      </div>

      {/* Description */}
      <p className="text-sm leading-relaxed mb-4 opacity-95">
        {card.description}
      </p>

      {/* Key Insights */}
      {card.key_insights.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-medium mb-2 opacity-90">Key Insights:</h4>
          <ul className="space-y-1">
            {card.key_insights.slice(0, 3).map((insight, index) => (
              <li key={index} className="text-xs flex items-start space-x-2">
                <span className="opacity-75">•</span>
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
          <span className="text-xs opacity-75">Completeness</span>
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
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      )}

      {/* Background Pattern */}
      <div className="absolute top-0 right-0 -mt-4 -mr-4 w-16 h-16 bg-white bg-opacity-10 rounded-full"></div>
      <div className="absolute bottom-0 left-0 -mb-4 -ml-4 w-12 h-12 bg-white bg-opacity-10 rounded-full"></div>
    </div>
  );
}