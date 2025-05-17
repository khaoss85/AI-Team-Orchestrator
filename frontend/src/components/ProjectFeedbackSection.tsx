import React from 'react';
import Link from 'next/link';

interface ProjectFeedbackSectionProps {
  workspaceId: string;
  feedbackRequests: any[];
}

export default function ProjectFeedbackSection({ workspaceId, feedbackRequests }: ProjectFeedbackSectionProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-lg font-semibold">Richieste di Feedback</h2>
          <p className="text-gray-500">
            {feedbackRequests.length > 0 
              ? `${feedbackRequests.length} richieste in attesa di risposta` 
              : 'Nessuna richiesta di feedback in sospeso'}
          </p>
        </div>
        
        <Link 
          href="/human-feedback"
          className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition"
        >
          Visualizza Tutte
        </Link>
      </div>
      
      {feedbackRequests.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
          <div className="text-5xl mb-3">💬</div>
          <p className="text-gray-600 text-lg mb-1">Nessuna richiesta in attesa</p>
          <p className="text-gray-500 text-sm">
            Verrai notificato quando gli agenti richiederanno il tuo input
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {feedbackRequests.slice(0, 3).map((request) => (
            <div 
              key={request.id} 
              className="border rounded-lg p-4 hover:shadow-md transition"
              style={{
                borderLeftWidth: '4px',
                borderLeftColor: request.priority === 'high' 
                  ? '#ef4444' // red-500
                  : request.priority === 'medium'
                  ? '#f59e0b' // amber-500
                  : '#60a5fa' // blue-400
              }}
            >
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-medium">{request.title}</h3>
                  <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                    {request.description}
                  </p>
                </div>
                <span className={`text-xs px-2 py-1 rounded-full ${
                  request.priority === 'high' 
                    ? 'bg-red-100 text-red-800' 
                    : request.priority === 'medium'
                    ? 'bg-amber-100 text-amber-800'
                    : 'bg-blue-100 text-blue-800'
                }`}>
                  {request.priority}
                </span>
              </div>
              
              <div className="mt-3 flex justify-between items-center">
                <div className="text-xs text-gray-500">
                  Scade il: {new Date(request.expires_at).toLocaleString('it-IT', {
                    day: 'numeric',
                    month: 'short',
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </div>
                <Link 
                  href={`/human-feedback?id=${request.id}`}
                  className="text-indigo-600 text-sm font-medium hover:text-indigo-800"
                >
                  Rispondi →
                </Link>
              </div>
            </div>
          ))}
          
          {feedbackRequests.length > 3 && (
            <div className="text-center pt-2">
              <Link 
                href="/human-feedback"
                className="text-indigo-600 text-sm font-medium hover:text-indigo-800"
              >
                Visualizza tutte le {feedbackRequests.length} richieste →
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
