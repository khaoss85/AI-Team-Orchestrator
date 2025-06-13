'use client';

import React, { useState, useEffect } from 'react';
import { api } from '@/utils/api';
import { FeedbackRequest, FeedbackResponse, ProposedAction } from '@/types';

interface HumanFeedbackDashboardProps {
  workspaceId?: string;
  assetContext?: {
    assetId: string;
    assetName: string;
    sourceTaskId: string;
  };
}

export default function HumanFeedbackDashboard({ workspaceId, assetContext }: HumanFeedbackDashboardProps) {
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
  }, [workspaceId, assetContext]);

  const fetchPendingRequests = async () => {
    try {
      setLoading(true);
      const requests = await api.humanFeedback.getPendingRequests(workspaceId);
      
      // Filter by asset context if provided
      const filteredRequests = assetContext 
        ? requests.filter(request => 
            // Check if the request is related to this specific asset/task
            request.context?.task_id === assetContext.sourceTaskId ||
            request.context?.asset_id === assetContext.assetId ||
            request.title.toLowerCase().includes(assetContext.assetName.toLowerCase())
          )
        : requests;
      
      setPendingRequests(filteredRequests);
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
      case 'critical_asset_verification': return '🔍';
      default: return '❓';
    }
  };

  const renderDeliverableContent = (content: any) => {
    if (!content || typeof content !== 'object') {
      return <div className="text-gray-500">Nessun contenuto disponibile</div>;
    }

    return (
      <div className="space-y-4">
        {Object.entries(content).map(([key, value]) => (
          <div key={key} className="border-l-4 border-blue-500 pl-4">
            <h4 className="font-medium text-gray-900 mb-2 capitalize">
              {key.replace(/_/g, ' ')}
            </h4>
            {renderContentValue(value)}
          </div>
        ))}
      </div>
    );
  };

  const renderContentValue = (value: any): React.ReactNode => {
    if (value === null || value === undefined) {
      return <span className="text-gray-400">Non disponibile</span>;
    }

    // Handle formatted list content (especially email sequences)
    if (typeof value === 'object' && value.total_count !== undefined && value.items) {
      return (
        <div>
          <div className="text-sm text-gray-600 mb-2">
            Totale: {value.total_count} elementi
          </div>
          <div className="space-y-3">
            {value.items.map((item: any, index: number) => (
              <div key={index} className="bg-white p-3 rounded border border-gray-200">
                {item.sequence_number && (
                  <div className="text-xs text-gray-500 mb-2">Sequenza #{item.sequence_number}</div>
                )}
                {renderEmailSequenceItem(item.content || item)}
              </div>
            ))}
          </div>
          {value.note && (
            <div className="text-xs text-gray-500 mt-2">{value.note}</div>
          )}
        </div>
      );
    }

    // Handle formatted dict content
    if (typeof value === 'object' && !Array.isArray(value)) {
      return (
        <div className="space-y-2">
          {Object.entries(value).map(([k, v]) => (
            <div key={k} className="flex">
              <span className="font-medium text-gray-700 min-w-32">{k}:</span>
              <span className="text-gray-900 ml-2">{renderSimpleValue(v)}</span>
            </div>
          ))}
        </div>
      );
    }

    // Handle arrays
    if (Array.isArray(value)) {
      return (
        <div className="space-y-1">
          {value.map((item, index) => (
            <div key={index} className="p-2 bg-white rounded border border-gray-100">
              {renderSimpleValue(item)}
            </div>
          ))}
        </div>
      );
    }

    return renderSimpleValue(value);
  };

  const renderEmailSequenceItem = (item: any) => {
    if (typeof item === 'object' && item !== null) {
      return (
        <div className="space-y-2">
          {item.subject && (
            <div>
              <span className="font-semibold text-gray-700">Oggetto:</span>
              <div className="mt-1 p-2 bg-blue-50 border-l-4 border-blue-400 text-gray-900">
                {item.subject}
              </div>
            </div>
          )}
          {item.body && (
            <div>
              <span className="font-semibold text-gray-700">Contenuto:</span>
              <div className="mt-1 p-3 bg-gray-50 rounded text-gray-900 whitespace-pre-wrap">
                {item.body}
              </div>
            </div>
          )}
          {item.call_to_action && (
            <div>
              <span className="font-semibold text-gray-700">Call-to-Action:</span>
              <div className="mt-1 p-2 bg-green-50 border-l-4 border-green-400 text-gray-900">
                {item.call_to_action}
              </div>
            </div>
          )}
          {item.timing && (
            <div className="text-sm text-gray-600">
              <span className="font-medium">Timing:</span> {item.timing}
            </div>
          )}
          {/* Handle other email fields */}
          {Object.entries(item).map(([key, value]) => {
            if (['subject', 'body', 'call_to_action', 'timing'].includes(key)) return null;
            return (
              <div key={key} className="text-sm">
                <span className="font-medium text-gray-600">{key}:</span>
                <span className="ml-2 text-gray-800">{renderSimpleValue(value)}</span>
              </div>
            );
          })}
        </div>
      );
    }
    return renderSimpleValue(item);
  };

  const renderSimpleValue = (value: any): string => {
    if (typeof value === 'string') {
      return value;
    }
    if (typeof value === 'number' || typeof value === 'boolean') {
      return String(value);
    }
    if (value === null || value === undefined) {
      return 'N/A';
    }
    return JSON.stringify(value, null, 2);
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
          <h2 className="text-xl font-semibold">
            {assetContext ? `Feedback for ${assetContext.assetName}` : 'Richieste di Feedback Umano'}
          </h2>
          <p className="text-gray-600">
            {assetContext 
              ? 'Asset-specific feedback requests and decisions'
              : 'Decisioni che richiedono supervisione umana'
            }
          </p>
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
          <p className="text-gray-500">
            {assetContext 
              ? `No feedback requests for ${assetContext.assetName}`
              : 'Nessuna richiesta di feedback pendente'
            }
          </p>
          <p className="text-sm text-gray-400 mt-2">
            {assetContext 
              ? 'This asset is working smoothly without human intervention needed'
              : 'Il sistema sta operando autonomamente'
            }
          </p>
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
              
              {/* Deliverable Content Preview */}
              {selectedRequest.context?.deliverable_preview?.content_for_review && (
                <div className="mb-6">
                  <h3 className="font-medium mb-3">📋 Contenuto da Verificare:</h3>
                  <div className="bg-gray-50 rounded-lg border p-4 max-h-96 overflow-y-auto">
                    {renderDeliverableContent(selectedRequest.context.deliverable_preview.content_for_review)}
                  </div>
                  
                  {/* Summary */}
                  {selectedRequest.context.deliverable_preview.summary && (
                    <div className="mt-3 text-sm text-gray-600">
                      <strong>Riassunto:</strong>
                      <ul className="list-disc list-inside mt-1">
                        {Object.entries(selectedRequest.context.deliverable_preview.summary).map(([key, value]) => (
                          <li key={key}>{key}: {value as string}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
              
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