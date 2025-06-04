import React from 'react';
import type { AgentProposal } from '@/types';

interface ProposalCardProps {
  proposal: AgentProposal;
  onApprove: (proposal: AgentProposal) => void;
  onReject: (proposal: AgentProposal) => void;
  onViewDetails: (proposal: AgentProposal) => void;
}

export const ProposalCard: React.FC<ProposalCardProps> = ({
  proposal,
  onApprove,
  onReject,
  onViewDetails
}) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready_for_review':
        return 'border-blue-500 bg-blue-50';
      case 'implementing':
        return 'border-orange-500 bg-orange-50';
      case 'approved':
        return 'border-green-500 bg-green-50';
      case 'rejected':
        return 'border-red-500 bg-red-50';
      case 'completed':
        return 'border-green-600 bg-green-100';
      default:
        return 'border-gray-300 bg-gray-50';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'analysis':
        return '📊';
      case 'deliverable':
        return '📋';
      case 'system':
        return '⚙️';
      case 'optimization':
        return '🚀';
      default:
        return '💡';
    }
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case 'high':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low':
        return 'bg-green-100 text-green-800 border-green-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 90) return 'text-green-600';
    if (confidence >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div
      className={`rounded-xl border-2 ${getStatusColor(proposal.status)} p-6 hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1`}
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="text-3xl">{getTypeIcon(proposal.type)}</div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{proposal.title}</h3>
            <p className="text-sm text-gray-600">
              {proposal.agentRole} • {proposal.timestamp}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <div className={`text-sm font-medium ${getConfidenceColor(proposal.confidence)}`}>
            {proposal.confidence}%
          </div>
          <div
            className={`w-3 h-3 rounded-full ${
              proposal.confidence > 90 ? 'bg-green-500' : proposal.confidence > 70 ? 'bg-yellow-500' : 'bg-red-500'
            }`}
          ></div>
        </div>
      </div>

      <div className="bg-white rounded-lg p-4 mb-4 border border-gray-200 hover:shadow-sm transition-shadow">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">Anteprima Output</span>
          <button onClick={() => onViewDetails(proposal)} className="text-xs text-blue-600 hover:text-blue-800 transition-colors">
            Dettagli completi →
          </button>
        </div>
        <div className="bg-gradient-to-r from-indigo-100 to-purple-100 rounded-lg p-3">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center shadow-sm">
              {proposal.preview.type === 'chart' && '📈'}
              {proposal.preview.type === 'calendar' && '📅'}
              {proposal.preview.type === 'flowchart' && '🔄'}
              {proposal.preview.type === 'document' && '📄'}
              {proposal.preview.type === 'dataset' && '📊'}
            </div>
            <span className="text-sm text-gray-700 flex-1">{proposal.preview.data}</span>
          </div>
        </div>
      </div>

      <div className="space-y-3 mb-4">
        <div className="bg-white rounded-lg p-3 border border-gray-100">
          <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Risultato</span>
          <p className="text-sm text-gray-900 mt-1">{proposal.output.summary}</p>
        </div>

        <div className="bg-blue-50 rounded-lg p-3 border border-blue-100">
          <span className="text-xs font-medium text-blue-600 uppercase tracking-wide">Asset Azionabile</span>
          <p className="text-sm text-blue-800 mt-1">📦 {proposal.output.actionable}</p>
        </div>

        <div className="bg-green-50 rounded-lg p-3 border border-green-100">
          <span className="text-xs font-medium text-green-600 uppercase tracking-wide">Impatto Business</span>
          <p className="text-sm text-green-800 font-medium mt-1">💰 {proposal.output.impact}</p>
        </div>
      </div>

      <div className="mb-4">
        <span className="text-sm font-medium text-gray-700 mb-3 block">Azioni Suggerite</span>
        <div className="space-y-2">
          {proposal.nextSteps.slice(0, 2).map((step, index) => (
            <div key={index} className="flex items-center justify-between bg-gray-50 rounded-lg p-3 hover:bg-gray-100 transition-colors">
              <span className="text-sm text-gray-800 flex-1">{step.action}</span>
              <div className="flex space-x-2 ml-3">
                <span className={`text-xs px-2 py-1 rounded-full border ${getUrgencyColor(step.urgency)}`}>{step.urgency}</span>
                {step.automated && (
                  <span className="text-xs px-2 py-1 rounded-full bg-purple-100 text-purple-800 border border-purple-200">🤖 Auto</span>
                )}
              </div>
            </div>
          ))}
          {proposal.nextSteps.length > 2 && (
            <div className="text-center">
              <button onClick={() => onViewDetails(proposal)} className="text-xs text-gray-500 hover:text-gray-700">
                +{proposal.nextSteps.length - 2} altre azioni
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="flex justify-between items-center mb-4 text-xs">
        <div className="flex items-center space-x-3">
          {proposal.metadata.riskLevel && (
            <span
              className={`px-2 py-1 rounded-full ${
                proposal.metadata.riskLevel === 'low'
                  ? 'bg-green-100 text-green-700'
                  : proposal.metadata.riskLevel === 'medium'
                  ? 'bg-yellow-100 text-yellow-700'
                  : 'bg-red-100 text-red-700'
              }`}
            >
              Rischio: {proposal.metadata.riskLevel}
            </span>
          )}
          {proposal.metadata.estimatedValue && proposal.metadata.estimatedValue > 0 && (
            <span className="px-2 py-1 rounded-full bg-purple-100 text-purple-700">Valore: €{proposal.metadata.estimatedValue.toLocaleString()}</span>
          )}
        </div>
      </div>

      {proposal.status === 'ready_for_review' && (
        <div className="flex space-x-3 pt-4 border-t border-gray-200">
          <button
            onClick={() => onApprove(proposal)}
            className="flex-1 bg-gradient-to-r from-green-600 to-green-700 text-white py-3 px-4 rounded-lg hover:from-green-700 hover:to-green-800 transition-all duration-200 font-medium shadow-sm hover:shadow-md"
          >
            ✅ Approva & Implementa
          </button>
          <button
            onClick={() => onReject(proposal)}
            className="flex-1 bg-gray-100 text-gray-800 py-3 px-4 rounded-lg hover:bg-gray-200 transition-all duration-200 font-medium border border-gray-200"
          >
            📝 Richiedi Modifiche
          </button>
        </div>
      )}

      {proposal.status === 'implementing' && (
        <div className="pt-4 border-t border-gray-200">
          <div className="flex items-center justify-center space-x-3 text-orange-600 bg-orange-50 py-3 rounded-lg">
            <div className="w-5 h-5 border-2 border-orange-600 border-r-transparent rounded-full animate-spin"></div>
            <span className="font-medium">Implementazione in corso...</span>
          </div>
        </div>
      )}

      {proposal.status === 'completed' && (
        <div className="pt-4 border-t border-gray-200">
          <div className="flex items-center justify-center space-x-3 text-green-600 bg-green-50 py-3 rounded-lg">
            <div className="w-5 h-5 text-green-600">✅</div>
            <span className="font-medium">Implementato con successo</span>
          </div>
        </div>
      )}
    </div>
  );
};

