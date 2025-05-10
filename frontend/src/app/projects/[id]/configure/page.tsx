'use client';

import React, { useState, useEffect, use } from 'react'; // Importa 'use' da React
import { useRouter } from 'next/navigation';
import { api } from '@/utils/api';
import { Workspace, DirectorTeamProposal, AgentSeniority } from '@/types';

// Aggiorna il tipo Props per riflettere che 'params' è una Promise
type Props = {
  params: Promise<{ id: string }>; // Indica che params è una Promise che risolverà in un oggetto { id: string }
  searchParams?: { [key: string]: string | string[] | undefined };
};

export default function ConfigureProjectPage({ params: paramsPromise, searchParams }: Props) {
  // Usa React.use() per "sbloccare" la Promise dei parametri
  const params = use(paramsPromise);
  const { id } = params; // Ora 'id' è accessibile dall'oggetto params risolto

  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [proposalLoading, setProposalLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [proposal, setProposal] = useState<DirectorTeamProposal | null>(null);

  const mockUserId = '123e4567-e89b-12d3-a456-426614174000';

  useEffect(() => {
    const fetchWorkspace = async () => {
      try {
        setLoading(true);
        // Usa 'id' risolto
        const data = await api.workspaces.get(id);
        setWorkspace(data);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch workspace:', err);
        setError('Impossibile caricare i dettagli del progetto. Riprova più tardi.');
        setWorkspace({
          id: id, // Usa 'id' risolto
          name: 'Progetto Marketing Digitale',
          description: 'Campagna di marketing sui social media',
          user_id: mockUserId,
          status: 'created',
          goal: 'Aumentare la visibilità del brand',
          budget: { max_amount: 1000, currency: 'EUR' },
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        });
      } finally {
        setLoading(false);
      }
    };

    if (id) { // Verifica 'id' risolto prima di fare il fetch
      fetchWorkspace();
    }
  }, [id]); // Usa 'id' risolto come dipendenza

  const handleCreateProposal = async () => {
    if (!workspace) return;

    try {
      setProposalLoading(true);
      setError(null);

      const directorConfig = {
        workspace_id: workspace.id, // workspace.id dovrebbe essere corretto qui
        goal: workspace.goal || 'Completare il progetto con successo',
        budget_constraint: workspace.budget || { max_amount: 1000, currency: 'EUR' },
        user_id: workspace.user_id
      };

      const data = await api.director.createProposal(directorConfig);
      setProposal(data);
    } catch (err) {
      console.error('Failed to create team proposal:', err);
      setError('Impossibile generare la proposta di team. Riprova più tardi.');

      if (workspace) {
        setProposal({
          workspace_id: workspace.id,
          agents: [
            {
              workspace_id: workspace.id,
              name: "Project Manager",
              role: "Project Management",
              seniority: "expert" as AgentSeniority,
              description: "Coordina l'intero progetto e gestisce gli handoff tra gli agenti",
              system_prompt: "Sei un project manager esperto che coordina un team di agenti specializzati."
            },
            {
              workspace_id: workspace.id,
              name: "Content Specialist",
              role: "Content Creation",
              seniority: "senior" as AgentSeniority,
              description: "Specialista nella creazione di contenuti di alta qualità",
              system_prompt: "Sei uno specialista nella creazione di contenuti marketing coinvolgenti."
            },
            {
              workspace_id: workspace.id,
              name: "Data Analyst",
              role: "Data Analysis",
              seniority: "senior" as AgentSeniority,
              description: "Analizza dati e crea visualizzazioni informative",
              system_prompt: "Sei un analista di dati specializzato nell'interpretazione e visualizzazione dei dati."
            }
          ],
          handoffs: [
            {
              source_agent_id: "00000000-0000-0000-0000-000000000000",
              target_agent_id: "00000000-0000-0000-0000-000000000000",
              description: "Handoff dei risultati dell'analisi per la creazione di contenuti"
            }
          ],
          estimated_cost: {
            total: 850,
            breakdown: {
              "Project Manager": 400,
              "Content Specialist": 250,
              "Data Analyst": 200
            }
          },
          rationale: "Team progettato per bilanciare competenze e vincoli di budget. Il PM esperto garantirà una gestione efficiente, mentre gli specialisti senior forniranno risultati di alta qualità a un costo ragionevole."
        });
      }
    } finally {
      setProposalLoading(false);
    }
  };

  const handleApproveProposal = async () => {
    if (!workspace || !proposal) return;

    try {
      setLoading(true);
      setError(null);

      await api.director.approveProposal(workspace.id, 'proposal-id');

      if (workspace) {
         router.push(`/projects/${workspace.id}`);
      }
    } catch (err) {
      console.error('Failed to approve team proposal:', err);
      setError('Impossibile approvare la proposta di team. Riprova più tardi.');

      if (workspace) {
        setTimeout(() => {
          router.push(`/projects/${workspace.id}`);
        }, 1000);
      }
    } finally {
      setLoading(false);
    }
  };

  const getSeniorityLabel = (seniority: AgentSeniority) => {
    switch(seniority) {
      case 'junior': return 'Junior';
      case 'senior': return 'Senior';
      case 'expert': return 'Expert';
      default: return seniority;
    }
  };

  const getSeniorityColor = (seniority: AgentSeniority) => {
    switch(seniority) {
      case 'junior': return 'bg-blue-100 text-blue-800';
      case 'senior': return 'bg-purple-100 text-purple-800';
      case 'expert': return 'bg-indigo-100 text-indigo-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading && !workspace) {
    return (
      <div className="container mx-auto max-w-4xl">
        <div className="text-center py-10">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-indigo-600 border-r-transparent"></div>
          <p className="mt-2 text-gray-600">Caricamento progetto...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-4xl">
      <h1 className="text-2xl font-semibold mb-1">Configura Team di Agenti</h1>
      <p className="text-gray-600 mb-6">
        Il direttore virtuale analizzerà il tuo progetto e proporrà un team di agenti ottimale.
      </p>

      {error && (
        <div className="bg-red-50 text-red-700 p-4 rounded-md mb-6">
          {error}
        </div>
      )}

      {workspace && (
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Dettagli Progetto</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <p className="text-sm text-gray-500">Nome</p>
              <p className="font-medium">{workspace.name}</p>
            </div>

            <div>
              <p className="text-sm text-gray-500">Stato</p>
              <p className="font-medium">
                <span className={`inline-block px-2 py-1 text-xs rounded-full ${
                  workspace.status === 'active' ? 'bg-green-100 text-green-800' :
                  workspace.status === 'created' ? 'bg-blue-100 text-blue-800' :
                  workspace.status === 'paused' ? 'bg-yellow-100 text-yellow-800' :
                  workspace.status === 'completed' ? 'bg-gray-100 text-gray-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {workspace.status === 'active' ? 'Attivo' :
                  workspace.status === 'created' ? 'Creato' :
                  workspace.status === 'paused' ? 'In pausa' :
                  workspace.status === 'completed' ? 'Completato' :
                  'Errore'}
                </span>
              </p>
            </div>

            <div>
              <p className="text-sm text-gray-500">Obiettivo</p>
              <p className="font-medium">{workspace.goal || 'Non specificato'}</p>
            </div>

            <div>
              <p className="text-sm text-gray-500">Budget</p>
              <p className="font-medium">
                {workspace.budget
                  ? `${workspace.budget.max_amount} ${workspace.budget.currency}`
                  : 'Non specificato'}
              </p>
            </div>
          </div>

          {!proposal && (
            <div className="mt-4">
              <button
                onClick={handleCreateProposal}
                className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition flex items-center"
                disabled={proposalLoading}
              >
                {proposalLoading ? (
                  <>
                    <div className="h-4 w-4 border-2 border-white border-r-transparent rounded-full animate-spin mr-2"></div>
                    Generazione proposta...
                  </>
                ) : (
                  'Genera Proposta Team'
                )}
              </button>
              <p className="mt-2 text-xs text-gray-500">
                Il direttore analizzerà il tuo progetto e proporrà un team di agenti ottimale.
              </p>
            </div>
          )}
        </div>
      )}

      {proposal && (
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h2 className="text-lg font-semibold mb-2">Proposta Team</h2>
          <p className="text-gray-600 mb-4">{proposal.rationale}</p>

          <div className="mb-6">
            <h3 className="text-md font-medium mb-2">Costo Stimato</h3>
            <div className="bg-gray-50 p-4 rounded-md">
              <div className="flex justify-between items-center mb-2">
                <span className="text-gray-600">Costo Totale:</span>
                <span className="font-semibold">{proposal.estimated_cost.total} EUR</span>
              </div>

              <div className="text-sm text-gray-600">
                <div className="mt-2 mb-1">Dettaglio costi:</div>
                <ul className="space-y-1">
                  {Object.entries(proposal.estimated_cost.breakdown).map(([role, cost]) => (
                    <li key={role} className="flex justify-between">
                      <span>{role}:</span>
                      <span>{cost} EUR</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          <h3 className="text-md font-medium mb-3">Agenti Proposti</h3>
          <div className="space-y-4 mb-6">
            {proposal.agents.map((agent, index) => (
              <div key={index} className="border border-gray-200 rounded-md p-4">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <h4 className="font-medium">{agent.name}</h4>
                    <p className="text-gray-600 text-sm">{agent.role}</p>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-full ${getSeniorityColor(agent.seniority)}`}>
                    {getSeniorityLabel(agent.seniority)}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-2">{agent.description}</p>
              </div>
            ))}
          </div>

          <div className="flex justify-end space-x-3">
            <button
              onClick={() => setProposal(null)}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md text-sm hover:bg-gray-200 transition"
              disabled={loading}
            >
              Rigenera Proposta
            </button>
            <button
              onClick={handleApproveProposal}
              className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition flex items-center"
              disabled={loading}
            >
              {loading ? (
                <>
                  <div className="h-4 w-4 border-2 border-white border-r-transparent rounded-full animate-spin mr-2"></div>
                  Creazione Team...
                </>
              ) : (
                'Approva e Crea Team'
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}