import React from 'react';
import { ProjectOutputExtended } from '@/types';

interface ActionableOutputCardProps {
  output: ProjectOutputExtended;
  onClick?: () => void;
}

export default function ActionableOutputCard({ output, onClick }: ActionableOutputCardProps) {
  const title = output.title || output.task_name;
  const summary = output.summary || output.output;
  const hasStructuredContent = output.visual_summary || (output.result && (output.result.tables || output.result.cards || output.result.metrics));

  return (
    <div className="bg-white border rounded-lg p-4 shadow-sm flex flex-col justify-between hover:shadow-md transition cursor-pointer" onClick={onClick}>
      <div>
        <div className="flex items-start justify-between mb-2">
          <h3 className="font-semibold text-gray-800 text-sm flex-1 mr-2">{title}</h3>
          {hasStructuredContent && (
            <span className="bg-indigo-100 text-indigo-700 text-xs px-2 py-1 rounded-full flex-shrink-0">
              📊 Rich Content
            </span>
          )}
        </div>
        
        {/* Show visual summary if available */}
        {output.visual_summary && (
          <div className="bg-gray-50 rounded p-2 mb-2 text-xs text-gray-700 space-y-1">
            {output.visual_summary.split('\n').map((line, idx) => (
              <div key={idx} className="flex items-start">
                <span className="mr-1">{line}</span>
              </div>
            ))}
          </div>
        )}
        
        {/* Show key insights if available */}
        {output.key_insights && output.key_insights.length > 0 && (
          <div className="mb-2">
            {output.key_insights.slice(0, 2).map((insight, idx) => (
              <div key={idx} className="text-xs text-indigo-600 flex items-start">
                <span className="mr-1">•</span>
                <span>{insight}</span>
              </div>
            ))}
          </div>
        )}
        
        {/* Fallback to summary */}
        {!output.visual_summary && !output.key_insights && summary && (
          <p className="text-sm text-gray-600 line-clamp-3 overflow-hidden">
            {summary.length > 160 ? summary.slice(0, 160) + '…' : summary}
          </p>
        )}
      </div>
      <button className="mt-3 text-indigo-600 text-sm hover:underline self-start" onClick={onClick}>
        View details
      </button>
    </div>
  );
}
