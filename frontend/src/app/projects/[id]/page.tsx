'use client';

import React, { useState, useEffect, use } from 'react';
import Link from 'next/link';
import { api } from '@/utils/api';
import { useOrchestration } from '@/hooks/useOrchestration';
import { OrchestrationCenter } from '@/components/orchestration/OrchestrationCenter';
import ProjectInsightsDashboard from '@/components/ProjectInsightsDashboard';
import ConfirmModal from '@/components/ConfirmModal';
import { useRouter } from 'next/navigation';

type Props = {
  params: Promise<{ id: string }>;
  searchParams?: { [key: string]: string | string[] | undefined };
};

export default function ProjectOrchestrationPage({ params: paramsPromise }: Props) {
  const router = useRouter();
  const params = use(paramsPromise);
  const workspaceId = params.id;

  const [workspace, setWorkspace] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [selectedView, setSelectedView] = useState<'orchestration' | 'insights'>('orchestration');
  const [startingTeam, setStartingTeam] = useState(false);

  const { proposals, stats, loading: orchestrationLoading, error: orchestrationError, actions } = useOrchestration(workspaceId);

  useEffect(() => {
    const fetchWorkspace = async () => {
      try {
        setLoading(true);
        const workspaceData = await api.workspaces.get(workspaceId);
        setWorkspace(workspaceData);
        setError(null);
      } catch (err) {
        console.error('Error fetching workspace:', err);
        setError(err instanceof Error ? err.message : 'Impossibile caricare il progetto');
      } finally {
        setLoading(false);
      }
    };

    if (workspaceId) {
      fetchWorkspace();
    }
  }, [workspaceId]);

  const handleDeleteProject = async () => {
    try {
      await api.workspaces.delete(workspaceId);
      router.push('/projects');
    } catch (err) {
      console.error('Error deleting project:', err);
    }
  };

  const handleStartTeam = async () => {
    try {
      setStartingTeam(true);
      await api.monitoring.startTeam(workspaceId);
      const updated = await api.workspaces.get(workspaceId);
      setWorkspace(updated);
      setError(null);
    } catch (err) {
      console.error('Error starting team:', err);
      setError(err instanceof Error ? err.message : 'Impossibile avviare il team');
    } finally {
      setStartingTeam(false);
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto">
        <div className="flex items-center justify-center py-20">
          <div className="text-center">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-indigo-600 border-r-transparent"></div>
            <p className="mt-4 text-gray-600">Caricamento centro di orchestrazione...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto">
        <div className="bg-red-50 text-red-700 p-6 rounded-lg mb-6">
          <div className="flex items-center">
            <span className="mr-2">⚠️</span>
            <div>
              <strong>Errore:</strong> {error}
            </div>
          </div>
        </div>
        <div className="flex space-x-4">
          <button onClick={() => router.push('/projects')} className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition">
            Torna alla lista progetti
          </button>
          <button onClick={() => window.location.reload()} className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition">
            Riprova
          </button>
        </div>
      </div>
    );
  }

  if (!workspace) {
    return (
      <div className="container mx-auto">
        <div className="text-center py-20">
          <div className="text-4xl mb-4">😕</div>
          <h2 className="text-xl font-medium mb-2">Progetto non trovato</h2>
          <p className="text-gray-500 mb-4">Non è stato possibile trovare il progetto richiesto.</p>
          <Link href="/projects" className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition">
            Torna alla lista progetti
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link href="/projects" className="text-indigo-600 hover:text-indigo-800 transition">
                ← Progetti
              </Link>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">{workspace.name}</h1>
                <p className="text-gray-600">{workspace.description}</p>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <div
                className={`px-3 py-1 rounded-full text-sm font-medium ${
                  workspace.status === 'active'
                    ? 'bg-green-100 text-green-800'
                    : workspace.status === 'created'
                    ? 'bg-blue-100 text-blue-800'
                    : workspace.status === 'paused'
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-gray-100 text-gray-800'
                }`}
              >
                {workspace.status === 'active' ? 'Attivo' : workspace.status === 'created' ? 'Creato' : workspace.status === 'paused' ? 'In pausa' : workspace.status}
              </div>

              {!orchestrationLoading && (
                <div className="flex space-x-3 text-sm">
                  <div className="text-center">
                    <div className="font-bold text-blue-600">{stats.pending}</div>
                    <div className="text-xs text-gray-500">Da rivedere</div>
                  </div>
                  <div className="text-center">
                    <div className="font-bold text-orange-600">{stats.implementing}</div>
                    <div className="text-xs text-gray-500">In corso</div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {workspace.goal && (
            <div className="mt-4 p-4 bg-indigo-50 border-l-4 border-indigo-500 rounded-r-md">
              <p className="text-sm text-indigo-900">
                <span className="font-medium">Obiettivo:</span> {workspace.goal}
              </p>
            </div>
          )}
        </div>
      </div>
      <div className="bg-white border-b border-gray-200">
        <div className="container mx-auto px-6">
          <nav className="flex space-x-8">
            <button
              onClick={() => setSelectedView('orchestration')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition ${
                selectedView === 'orchestration' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              🎯 Centro di Orchestrazione
              {stats.pending > 0 && <span className="ml-2 bg-red-500 text-white text-xs px-2 py-1 rounded-full">{stats.pending}</span>}
            </button>

            <button
              onClick={() => setSelectedView('insights')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition ${
                selectedView === 'insights' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              📊 Insights & Metriche
            </button>

            <div className="ml-auto flex items-center space-x-4">
              <Link href={`/projects/${workspaceId}/deliverables`} className="text-sm text-gray-600 hover:text-gray-800 transition">
                📋 Deliverable
              </Link>
              <Link href={`/projects/${workspaceId}/assets`} className="text-sm text-gray-600 hover:text-gray-800 transition">
                📦 Asset
              </Link>
              {workspace.status === 'created' && (
                <button
                  onClick={handleStartTeam}
                  className="text-sm bg-green-600 text-white px-3 py-1 rounded-md hover:bg-green-700 transition disabled:opacity-50"
                  disabled={startingTeam}
                >
                  {startingTeam ? 'Avvio...' : '🚀 Avvia Team'}
                </button>
              )}
              <button onClick={() => setIsDeleteModalOpen(true)} className="text-sm text-red-600 hover:text-red-800 transition">
                🗑️ Elimina
              </button>
            </div>
          </nav>
        </div>
      </div>

      <div className="container mx-auto">
        {selectedView === 'orchestration' && (
          <OrchestrationCenter
            workspaceId={workspaceId}
            proposals={proposals}
            stats={stats}
            loading={orchestrationLoading}
            error={orchestrationError}
            onApprove={actions.approve}
            onReject={actions.reject}
            onRefresh={actions.refresh}
          />
        )}

        {selectedView === 'insights' && (
          <div className="p-6">
            <ProjectInsightsDashboard workspaceId={workspaceId} />
          </div>
        )}
      </div>

      <ConfirmModal
        isOpen={isDeleteModalOpen}
        title="Elimina progetto"
        message={`Sei sicuro di voler eliminare il progetto "${workspace?.name}"? Questa azione eliminerà anche tutti gli agenti, asset e i dati associati. Questa azione non può essere annullata.`}
        confirmText="Elimina"
        cancelText="Annulla"
        onConfirm={handleDeleteProject}
        onCancel={() => setIsDeleteModalOpen(false)}
      />
    </div>
  );
}
