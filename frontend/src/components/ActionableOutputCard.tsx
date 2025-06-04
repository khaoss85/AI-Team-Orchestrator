import React from 'react';
import { ProjectOutputExtended } from '@/types';

interface ActionableOutputCardProps {
  output: ProjectOutputExtended;
  onClick?: () => void;
}

export default function ActionableOutputCard({ output, onClick }: ActionableOutputCardProps) {
  const title = output.title || output.task_name;
  const summary = output.summary || output.output;

  return (
    <div className="bg-white border rounded-lg p-4 shadow-sm flex flex-col justify-between hover:shadow-md transition cursor-pointer" onClick={onClick}>
      <div>
        <h3 className="font-semibold text-gray-800 text-sm mb-1 truncate">{title}</h3>
        {summary && (
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
