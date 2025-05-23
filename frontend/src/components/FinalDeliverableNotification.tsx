// frontend/src/components/FinalDeliverableNotification.tsx
import React from 'react';
import Link from 'next/link';

interface FinalDeliverableNotificationProps {
  workspaceId: string;
  finalDeliverables: any[];
  onDismiss?: () => void;
}

export default function FinalDeliverableNotification({ 
  workspaceId, 
  finalDeliverables, 
  onDismiss 
}: FinalDeliverableNotificationProps) {
  if (finalDeliverables.length === 0) return null;
  
  return (
    <div className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg shadow-lg p-6 mb-6">
      <div className="flex items-start justify-between">
        <div className="flex items-start">
          <div className="bg-white bg-opacity-20 rounded-full p-3 mr-4">
            <span className="text-2xl">🎯</span>
          </div>
          <div>
            <h3 className="text-lg font-semibold mb-2">
              Deliverable Finali Pronti per la Revisione!
            </h3>
            <p className="text-indigo-100 mb-4">
              Il tuo team ha completato {finalDeliverables.length} deliverable{finalDeliverables.length > 1 ? 's' : ''} finale{finalDeliverables.length > 1 ? 'i' : ''} 
              che richie{finalDeliverables.length > 1 ? 'dono' : 'de'} la tua approvazione.
            </p>
            
            <div className="flex flex-wrap gap-2 mb-4">
              {finalDeliverables.slice(0, 3).map(deliverable => (
                <div key={deliverable.id} className="bg-white bg-opacity-20 px-3 py-1 rounded-full text-sm">
                  {deliverable.title}
                </div>
              ))}
              {finalDeliverables.length > 3 && (
                <div className="bg-white bg-opacity-20 px-3 py-1 rounded-full text-sm">
                  +{finalDeliverables.length - 3} altri
                </div>
              )}
            </div>
            
            <div className="flex space-x-3">
              <Link 
                href={`/projects/${workspaceId}/deliverables`}
                className="bg-white text-indigo-600 px-4 py-2 rounded-md font-medium hover:bg-indigo-50 transition"
              >
                Visualizza Deliverables
              </Link>
              <button 
                onClick={() => {
                  // Switch to results section
                  document.querySelector('[data-section="results"]')?.click();
                }}
                className="bg-white bg-opacity-20 text-white px-4 py-2 rounded-md font-medium hover:bg-white hover:bg-opacity-30 transition"
              >
                Vai ai Risultati
              </button>
            </div>
          </div>
        </div>
        
        {onDismiss && (
          <button 
            onClick={onDismiss}
            className="text-white hover:text-indigo-200 transition"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}

// Aggiungi questo nella pagina principale del progetto dopo l'header:
// {/* Notification for final deliverables */}
// {(() => {
//   const finalDeliverables = projectResults.filter(r => r.type === 'final_deliverable');
//   return finalDeliverables.length > 0 && (
//     <FinalDeliverableNotification 
//       workspaceId={workspaceId}
//       finalDeliverables={finalDeliverables}
//     />
//   );
// })()}