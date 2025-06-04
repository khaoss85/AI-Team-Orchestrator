import React, { useState } from 'react';
import { AgentProposal } from '@/hooks/useOrchestration';

interface ProposalViewerProps {
  proposal: AgentProposal;
  onClose: () => void;
  onApprove?: (proposal: AgentProposal) => void;
  onReject?: (proposal: AgentProposal) => void;
}

export const ProposalViewer: React.FC<ProposalViewerProps> = ({ proposal, onClose, onApprove, onReject }) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'technical' | 'nextSteps'>('overview');

  const tabs = [
    { id: 'overview', label: '👀 Overview', icon: '👀' },
    { id: 'technical', label: '🔧 Dettagli Tecnici', icon: '🔧' },
    { id: 'nextSteps', label: '🚀 Prossimi Passi', icon: '🚀' }
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-5xl w-full max-h-[90vh] overflow-hidden">
        <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-gradient-to-r from-indigo-50 to-purple-50">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center shadow-md">
              <span className="text-2xl">
                {proposal.type === 'analysis' && '📊'}
                {proposal.type === 'deliverable' && '📋'}
                {proposal.type === 'system' && '⚙️'}
                {proposal.type === 'optimization' && '🚀'}
              </span>
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">{proposal.title}</h2>
              <p className="text-gray-600">
                {proposal.agentRole} • {proposal.timestamp}
              </p>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-2xl font-bold p-2 hover:bg-gray-100 rounded-lg transition">
            ✕
          </button>
        </div>

        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`py-4 px-2 border-b-2 font-medium text-sm transition ${
                  activeTab === tab.id ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gradient-to-br from-green-50 to-emerald-50 p-4 rounded-lg border border-green-200">
                  <h3 className="font-semibold text-green-800 mb-2">Confidenza</h3>
                  <div className="text-3xl font-bold text-green-900">{proposal.confidence}%</div>
                </div>

                {proposal.metadata.estimatedValue && (
                  <div className="bg-gradient-to-br from-purple-50 to-pink-50 p-4 rounded-lg border border-purple-200">
                    <h3 className="font-semibold text-purple-800 mb-2">Valore Stimato</h3>
                    <div className="text-3xl font-bold text-purple-900">€{proposal.metadata.estimatedValue.toLocaleString()}</div>
                  </div>
                )}

                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-4 rounded-lg border border-blue-200">
                  <h3 className="font-semibold text-blue-800 mb-2">Livello Rischio</h3>
                  <div
                    className={`text-2xl font-bold ${
                      proposal.metadata.riskLevel === 'low' ? 'text-green-600' : proposal.metadata.riskLevel === 'medium' ? 'text-yellow-600' : 'text-red-600'
                    }`}
                  >
                    {proposal.metadata.riskLevel?.toUpperCase()}
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <div className="bg-gradient-to-r from-indigo-50 to-blue-50 p-6 rounded-lg border border-indigo-200">
                  <h3 className="font-semibold text-indigo-800 text-lg mb-3">📋 Risultato Principale</h3>
                  <p className="text-indigo-900 leading-relaxed">{proposal.output.summary}</p>
                </div>

                <div className="bg-gradient-to-r from-green-50 to-emerald-50 p-6 rounded-lg border border-green-200">
                  <h3 className="font-semibold text-green-800 text-lg mb-3">📦 Asset Azionabile</h3>
                  <p className="text-green-900 leading-relaxed">{proposal.output.actionable}</p>
                </div>

                <div className="bg-gradient-to-r from-purple-50 to-pink-50 p-6 rounded-lg border border-purple-200">
                  <h3 className="font-semibold text-purple-800 text-lg mb-3">💰 Impatto Business</h3>
                  <p className="text-purple-900 leading-relaxed">{proposal.output.impact}</p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'technical' && (
            <div className="space-y-6">
              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="font-semibold text-gray-800 mb-4">Dettagli Tecnici</h3>
                <div className="space-y-4">
                  <div>
                    <span className="text-sm font-medium text-gray-600">Task ID Origine:</span>
                    <p className="font-mono text-sm bg-white p-2 rounded border">{proposal.metadata.sourceTaskId}</p>
                  </div>

                  <div>
                    <span className="text-sm font-medium text-gray-600">Timestamp Creazione:</span>
                    <p className="text-sm text-gray-800">{new Date(proposal.metadata.createdAt).toLocaleString('it-IT')}</p>
                  </div>

                  <div>
                    <span className="text-sm font-medium text-gray-600">Ultimo Aggiornamento:</span>
                    <p className="text-sm text-gray-800">{new Date(proposal.metadata.updatedAt).toLocaleString('it-IT')}</p>
                  </div>
                </div>
              </div>

              {proposal.output.technicalDetails && (
                <div className="bg-gray-900 rounded-lg p-6">
                  <h3 className="font-semibold text-white mb-4">Output Raw</h3>
                  <pre className="text-green-400 text-sm overflow-auto max-h-64">{JSON.stringify(proposal.output.technicalDetails, null, 2)}</pre>
                </div>
              )}
            </div>
          )}

          {activeTab === 'nextSteps' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Prossimi Passi Dettagliati</h3>

              {proposal.nextSteps.map((step, index) => (
                <div key={index} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition">
                  <div className="flex items-start justify-between mb-3">
                    <h4 className="font-medium text-gray-900 flex-1">{step.action}</h4>
                    <div className="flex space-x-2 ml-4">
                      <span
                        className={`text-xs px-2 py-1 rounded-full ${
                          step.urgency === 'high' ? 'bg-red-100 text-red-800' : step.urgency === 'medium' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'
                        }`}
                      >
                        {step.urgency} priority
                      </span>
                      <span className="text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-700">{step.effort} effort</span>
                      {step.automated && (
                        <span className="text-xs px-2 py-1 rounded-full bg-purple-100 text-purple-800">🤖 Automatizzabile</span>
                      )}
                    </div>
                  </div>

                  <div className="text-sm text-gray-600">Priorità {index + 1} di {proposal.nextSteps.length}</div>
                </div>
              ))}
            </div>
          )}
        </div>

        {proposal.status === 'ready_for_review' && onApprove && onReject && (
          <div className="border-t border-gray-200 px-6 py-4 bg-gray-50 flex space-x-4">
            <button onClick={() => onReject(proposal)} className="flex-1 bg-gray-100 text-gray-800 py-3 px-6 rounded-lg hover:bg-gray-200 transition font-medium">
              📝 Richiedi Modifiche
            </button>
            <button
              onClick={() => onApprove(proposal)}
              className="flex-1 bg-gradient-to-r from-green-600 to-green-700 text-white py-3 px-6 rounded-lg hover:from-green-700 hover:to-green-800 transition font-medium shadow-sm"
            >
              ✅ Approva & Implementa
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

