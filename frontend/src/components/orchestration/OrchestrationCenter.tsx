import React, { useState } from 'react';
import type { AgentProposal, OrchestrationStats } from '@/types';
import { ProposalCard } from './ProposalCard';
import { ProposalViewer } from './ProposalViewer';

interface OrchestrationCenterProps {
  workspaceId: string;
  proposals: AgentProposal[];
  stats: OrchestrationStats;
  loading: boolean;
  error: string | null;
  onApprove: (proposalId: string) => Promise<boolean>;
  onReject: (proposalId: string, reason?: string) => Promise<boolean>;
  onRefresh: () => void;
}

export const OrchestrationCenter: React.FC<OrchestrationCenterProps> = ({
  workspaceId,
  proposals,
  stats,
  loading,
  error,
  onApprove,
  onReject,
  onRefresh
}) => {
  const [selectedProposal, setSelectedProposal] = useState<AgentProposal | null>(null);
  const [filter, setFilter] = useState<'all' | 'ready_for_review' | 'implementing' | 'completed'>('all');
  const [rejectModalOpen, setRejectModalOpen] = useState<{ open: boolean; proposal: AgentProposal | null }>({
    open: false,
    proposal: null
  });
  const [rejectReason, setRejectReason] = useState('');

  const filteredProposals = proposals.filter(proposal => {
    if (filter === 'all') return true;
    return proposal.status === filter;
  });

  const groupedProposals = {
    urgent: filteredProposals.filter(
      p => p.status === 'ready_for_review' && p.nextSteps.some(step => step.urgency === 'high')
    ),
    normal: filteredProposals.filter(
      p => p.status === 'ready_for_review' && !p.nextSteps.some(step => step.urgency === 'high')
    ),
    implementing: filteredProposals.filter(p => p.status === 'implementing'),
    completed: filteredProposals.filter(p => p.status === 'completed')
  };

  const handleApprove = async (proposal: AgentProposal) => {
    const success = await onApprove(proposal.id);
    if (success) {
      console.log(`Proposal ${proposal.id} approved successfully`);
    }
  };

  const handleReject = (proposal: AgentProposal) => {
    setRejectModalOpen({ open: true, proposal });
  };

  const confirmReject = async () => {
    if (rejectModalOpen.proposal) {
      const success = await onReject(rejectModalOpen.proposal.id, rejectReason);
      if (success) {
        setRejectModalOpen({ open: false, proposal: null });
        setRejectReason('');
      }
    }
  };

  const handleViewDetails = (proposal: AgentProposal) => {
    setSelectedProposal(proposal);
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center py-20">
          <div className="text-center">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-indigo-600 border-r-transparent"></div>
            <p className="mt-4 text-gray-600">Caricamento proposte degli agenti...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 text-red-700 p-6 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <span className="mr-2">⚠️</span>
              <span>{error}</span>
            </div>
            <button onClick={onRefresh} className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition">
              Riprova
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Sala Regia Agenti</h2>
            <p className="text-gray-600">Decisioni e implementazioni in tempo reale</p>
          </div>

          <div className="flex items-center space-x-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{stats.pending}</div>
              <div className="text-xs text-gray-500">Richiedono Decisione</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{stats.implementing}</div>
              <div className="text-xs text-gray-500">In Implementazione</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{stats.completed}</div>
              <div className="text-xs text-gray-500">Completati</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{stats.avgConfidence}%</div>
              <div className="text-xs text-gray-500">Confidence Media</div>
            </div>
            {stats.totalEstimatedValue > 0 && (
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">€{stats.totalEstimatedValue.toLocaleString()}</div>
                <div className="text-xs text-gray-500">Valore Stimato</div>
              </div>
            )}
          </div>

          <button onClick={onRefresh} className="px-4 py-2 bg-indigo-50 text-indigo-600 rounded-md hover:bg-indigo-100 transition flex items-center space-x-2">
            <span>🔄</span>
            <span>Aggiorna</span>
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
        <div className="flex space-x-2">
          {[
            { key: 'all', label: 'Tutti', count: stats.total },
            { key: 'ready_for_review', label: 'Da Decidere', count: stats.pending },
            { key: 'implementing', label: 'In Implementazione', count: stats.implementing },
            { key: 'completed', label: 'Completati', count: stats.completed }
          ].map(({ key, label, count }) => (
            <button
              key={key}
              onClick={() => setFilter(key as any)}
              className={`px-4 py-2 rounded-lg font-medium text-sm transition ${
                filter === key ? 'bg-indigo-600 text-white shadow-md' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {label} ({count})
            </button>
          ))}
        </div>
      </div>

      {filteredProposals.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <div className="text-6xl mb-4">🎯</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            {filter === 'all' ? 'Nessuna proposta disponibile' : filter === 'ready_for_review' ? 'Nessuna proposta da rivedere' : filter === 'implementing' ? 'Nessuna implementazione in corso' : 'Nessuna proposta completata'}
          </h3>
          <p className="text-gray-500 mb-6">
            {filter === 'ready_for_review' ? 'I tuoi agenti stanno lavorando sulle prossime proposte' : 'Cambia filtro per vedere altre proposte'}
          </p>
          {filter !== 'all' && (
            <button onClick={() => setFilter('all')} className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition">
              Mostra Tutte le Proposte
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-8">
          {groupedProposals.urgent.length > 0 && (
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <span className="text-lg font-semibold text-red-600">🚨 Richiedono Decisione Urgente</span>
                <span className="bg-red-100 text-red-800 text-sm px-2 py-1 rounded-full">{groupedProposals.urgent.length}</span>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                {groupedProposals.urgent.map(proposal => (
                  <ProposalCard key={proposal.id} proposal={proposal} onApprove={handleApprove} onReject={handleReject} onViewDetails={handleViewDetails} />
                ))}
              </div>
            </div>
          )}

          {groupedProposals.normal.length > 0 && (
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <span className="text-lg font-semibold text-blue-600">💡 Proposte da Rivedere</span>
                <span className="bg-blue-100 text-blue-800 text-sm px-2 py-1 rounded-full">{groupedProposals.normal.length}</span>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                {groupedProposals.normal.map(proposal => (
                  <ProposalCard key={proposal.id} proposal={proposal} onApprove={handleApprove} onReject={handleReject} onViewDetails={handleViewDetails} />
                ))}
              </div>
            </div>
          )}

          {groupedProposals.implementing.length > 0 && (
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <span className="text-lg font-semibold text-orange-600">⚙️ In Implementazione</span>
                <span className="bg-orange-100 text-orange-800 text-sm px-2 py-1 rounded-full">{groupedProposals.implementing.length}</span>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                {groupedProposals.implementing.map(proposal => (
                  <ProposalCard key={proposal.id} proposal={proposal} onApprove={handleApprove} onReject={handleReject} onViewDetails={handleViewDetails} />
                ))}
              </div>
            </div>
          )}

          {groupedProposals.completed.length > 0 && filter !== 'ready_for_review' && filter !== 'implementing' && (
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <span className="text-lg font-semibold text-green-600">✅ Implementati con Successo</span>
                <span className="bg-green-100 text-green-800 text-sm px-2 py-1 rounded-full">{groupedProposals.completed.length}</span>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                {groupedProposals.completed.map(proposal => (
                  <ProposalCard key={proposal.id} proposal={proposal} onApprove={handleApprove} onReject={handleReject} onViewDetails={handleViewDetails} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {selectedProposal && (
        <ProposalViewer
          proposal={selectedProposal}
          onClose={() => setSelectedProposal(null)}
          onApprove={selectedProposal.status === 'ready_for_review' ? handleApprove : undefined}
          onReject={selectedProposal.status === 'ready_for_review' ? handleReject : undefined}
        />
      )}

      {rejectModalOpen.open && rejectModalOpen.proposal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6">
            <h3 className="text-lg font-semibold mb-4">Richiedi Modifiche</h3>
            <p className="text-gray-600 mb-4">Perché vuoi richiedere modifiche a "{rejectModalOpen.proposal.title}"?</p>
            <textarea
              value={rejectReason}
              onChange={e => setRejectReason(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
              rows={4}
              placeholder="Descrivi le modifiche richieste..."
            />
            <div className="flex space-x-3 mt-6">
              <button onClick={() => setRejectModalOpen({ open: false, proposal: null })} className="flex-1 px-4 py-2 bg-gray-100 text-gray-800 rounded-md hover:bg-gray-200 transition">
                Annulla
              </button>
              <button
                onClick={confirmReject}
                disabled={!rejectReason.trim()}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Invia Richiesta
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

