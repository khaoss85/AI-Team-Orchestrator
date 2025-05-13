'use client';

import React, { useState, useEffect } from 'react';
import { api } from '@/utils/api';
import { FeedbackRequest, FeedbackResponse, ProposedAction } from '@/types';

interface HumanFeedbackDashboardProps {
  workspaceId?: string;
}

export default function HumanFeedbackDashboard({ workspaceId }: HumanFeedbackDashboardProps) {
  const [pendingRequests, setPendingRequests] = useState<FeedbackRequest[]>([]);
  const [selectedRequest, setSelectedRequest] = useState<FeedbackRequest | null>(null);
  const [response, setResponse] = useState<Partial<FeedbackResponse>>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPendingRequests();
    const interval = setInterval(fetchPendingRequests, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [workspaceId]);

  const fetchPendingRequests = async () => {
    try {
      setLoading(true);
      const requests = await api.humanFeedback.getPendingRequests(workspaceId);
      setPendingRequests(requests);
      setError(null);
    } catch (err) {
      console.error('Error fetching pending requests:', err);
      setError('Impossibile caricare le richieste di feedback');
    } finally {
      setLoading(false);
    }
  };

  const handleResponse = async (approved: boolean) => {
    if (!selectedRequest) return;

    try {
      setSubmitting(true);
      
      const responseData: FeedbackResponse = {
        approved,
        status: approved ? 'approved' : 'rejected',
        comment: response.comment || '',
        modifications: response.modifications || [],
        reason: !approved ? response.reason : undefined
      };

      await api.humanFeedback.respondToRequest(selectedRequest.id, responseData);
      await fetchPendingRequests();
      setSelectedRequest(null);
      setResponse({});
      setError(null);
    } catch (err) {
      console.error('Error responding to request:', err);
      setError('Errore durante la risposta alla richiesta');
    } finally {
      setSubmitting(false);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800 border-red-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low': return 'bg-green-100 text-green-800 border-green-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getRequestTypeIcon = (type: string) => {
    switch (type) {
      case 'task_approval': return '✅';
      case 'strategy_review': return '📋';
      case 'intervention_required': return '🚨';
      case 'priority_decision': return '⚡';
      case 'resource_allocation': return '💰';
      default: return '❓';
    }
  };

  const formatTimeRemaining = (expiresAt: string) => {
    const now = new Date();
    const expires = new Date(expiresAt);
    const diffMs = expires.getTime() - now.getTime();
    
    if (diffMs <= 0) return 'Scaduto';
    
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
    
    if (diffHours > 0) return `${diffHours}h ${diffMinutes}m rimanenti`;
    return `${diffMinutes}m rimanenti`;
  };

  if (loading && pendingRequests.length === 0) {
    return (
      <div className="text-center py-10">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-indigo-600 border-r-transparent"></div>
        <p className="mt-2 text-gray-600">Caricamento richieste di feedback...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
          {error}
        </div>
      )}

      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-semibold">Richieste di Feedback Umano</h2>
          <p className="text-gray-600">Decisioni che richiedono supervisione umana</p>
        </div>
        <button
          onClick={fetchPendingRequests}
          className="px-4 py-2 bg-indigo-50 text-indigo-600 rounded-md text-sm hover:bg-indigo-100 transition"
        >
          Aggiorna
        </button>
      </div>
      
      {pendingRequests.length === 0 ? (
        <div className="text-center py-10 bg-white rounded-lg shadow-sm">
          <div className="text-4xl mb-4">✅</div>
          <p className="text-gray-500">Nessuna richiesta di feedback pendente</p>
          <p className="text-sm text-gray-400 mt-2">Il sistema sta operando autonomamente</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Request List */}
          <div className="space-y-4">
            <h3 className="font-medium">Richieste Pendenti ({pendingRequests.length})</h3>
            {pendingRequests.map((request) => (
              <div
                key={request.id}
                className={`p-4 border rounded-lg cursor-pointer transition-all ${
                  selectedRequest?.id === request.id
                    ? 'border-indigo-500 bg-indigo-50 shadow-md'
                    : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm'
                }`}
                onClick={() => setSelectedRequest(request)}
              >
                <div className="flex justify-between items-start mb-3">
                  <div className="flex items-center">
                    <span className="text-lg mr-2">{getRequestTypeIcon(request.request_type)}</span>
                    <h4 className="font-medium">{request.title}</h4>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-full ${getPriorityColor(request.priority)}`}>
                    {request.priority.toUpperCase()}
                  </span>
                </div>
                
                <p className="text-sm text-gray-600 mb-3">{request.description.substring(0, 150)}...</p>
                
                <div className="flex justify-between items-center text-xs text-gray-500">
                  <span>{request.proposed_actions.length} azioni proposte</span>
                  <span className={formatTimeRemaining(request.expires_at).includes('Scaduto') ? 'text-red-500' : ''}>
                    {formatTimeRemaining(request.expires_at)}
                  </span>
                </div>
              </div>
            ))}
          </div>
          
          {/* Request Details */}
          {selectedRequest && (
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <div className="flex items-center mb-4">
                <span className="text-2xl mr-3">{getRequestTypeIcon(selectedRequest.request_type)}</span>
                <div>
                  <h2 className="text-xl font-semibold">{selectedRequest.title}</h2>
                  <p className="text-sm text-gray-500">{selectedRequest.request_type.replace('_', ' ')}</p>
                </div>
              </div>
              
              <p className="text-gray-700 mb-4">{selectedRequest.description}</p>
              
              <div className="mb-6">
                <h3 className="font-medium mb-3">Azioni Proposte:</h3>
                <div className="space-y-3">
                  {selectedRequest.proposed_actions.map((action, index) => (
                    <div key={index} className="p-4 bg-gray-50 rounded-lg border">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <span className="font-medium text-indigo-700">{action.type}</span>
                          {action.task_name && (
                            <p className="text-gray-900 mt-1">{action.task_name}</p>
                          )}
                        </div>
                        {action.priority && (
                          <span className={`text-xs px-2 py-1 rounded-full ${getPriorityColor(action.priority)}`}>
                            {action.priority}
                          </span>
                        )}
                      </div>
                      {action.description && (
                        <p className="text-sm text-gray-600 mt-2">{action.description}</p>
                      )}
                      {action.target_role && (
                        <p className="text-xs text-gray-500 mt-1">Target: {action.target_role}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="mb-6">
                <label className="block text-sm font-medium mb-2">Commenti/Feedback:</label>
                <textarea
                  value={response.comment || ''}
                  onChange={(e) => setResponse({...response, comment: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  rows={3}
                  placeholder="Aggiungi commenti o suggerimenti..."
                />
              </div>
              
              {!response.approved && (
                <div className="mb-6">
                  <label className="block text-sm font-medium mb-2">Motivo del rifiuto:</label>
                  <input
                    type="text"
                    value={response.reason || ''}
                    onChange={(e) => setResponse({...response, reason: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                    placeholder="Specifica il motivo del rifiuto"
                  />
                </div>
              )}
              
              <div className="flex space-x-3">
                <button
                  onClick={() => handleResponse(true)}
                  disabled={submitting}
                  className="flex-1 py-2 px-4 bg-green-600 text-white rounded-md hover:bg-green-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                >
                  {submitting ? (
                    <>
                      <div className="h-4 w-4 border-2 border-white border-r-transparent rounded-full animate-spin mr-2"></div>
                      Approvo...
                    </>
                  ) : (
                    '✅ Approva'
                  )}
                </button>
                <button
                  onClick={() => handleResponse(false)}
                  disabled={submitting}
                  className="flex-1 py-2 px-4 bg-red-600 text-white rounded-md hover:bg-red-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                >
                  {submitting ? (
                    <>
                      <div className="h-4 w-4 border-2 border-white border-r-transparent rounded-full animate-spin mr-2"></div>
                      Rifiuto...
                    </>
                  ) : (
                    '❌ Rifiuta'
                  )}
                </button>
              </div>
              
              <div className="mt-4 pt-4 border-t">
                <p className="text-xs text-gray-500">
                  Creato: {new Date(selectedRequest.created_at).toLocaleString('it-IT')}
                </p>
                <p className="text-xs text-gray-500">
                  Scade: {new Date(selectedRequest.expires_at).toLocaleString('it-IT')}
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}