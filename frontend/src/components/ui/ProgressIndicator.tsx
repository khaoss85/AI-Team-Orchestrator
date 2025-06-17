'use client';

import React from 'react';

interface ProgressIndicatorProps {
  progress: number;
  message: string;
  status: string;
  className?: string;
}

export function ProgressIndicator({ progress, message, status, className = '' }: ProgressIndicatorProps) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'analyzing':
        return '🧠';
      case 'extracting_metrics':
        return '📊';
      case 'identifying_deliverables':
        return '📋';
      case 'analyzing_deliverable':
        return '🤖';
      case 'creating_plan':
        return '📅';
      case 'analyzing_risks':
        return '⚠️';
      case 'completed':
        return '✅';
      default:
        return '🔄';
    }
  };

  const getProgressColor = (progress: number) => {
    if (progress < 30) return 'bg-blue-500';
    if (progress < 60) return 'bg-yellow-500';
    if (progress < 90) return 'bg-orange-500';
    return 'bg-green-500';
  };

  return (
    <div className={`w-full max-w-md mx-auto bg-white rounded-lg shadow-sm border border-gray-200 p-4 ${className}`}>
      <div className="flex items-center gap-3 mb-3">
        <span className="text-2xl">{getStatusIcon(status)}</span>
        <div className="flex-1">
          <div className="flex justify-between items-center mb-1">
            <span className="text-sm font-medium text-gray-700">Analisi AI in corso</span>
            <span className="text-sm font-semibold text-gray-600">{progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className={`h-2 rounded-full transition-all duration-500 ease-out ${getProgressColor(progress)}`}
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </div>
      
      <p className="text-sm text-gray-600 text-center">
        {message}
      </p>
      
      {progress === 100 && (
        <div className="mt-3 flex items-center justify-center text-green-600">
          <span className="text-sm font-medium">Analisi completata!</span>
        </div>
      )}
    </div>
  );
}