// frontend/src/app/projects/[id]/page.tsx
'use client';

import React, { useState, useEffect, use } from 'react';
import Link from 'next/link';
import { api } from '@/utils/api';
import { Workspace, Agent, Task } from '@/types';
import ConfirmModal from '@/components/ConfirmModal';
import ProjectDashboard from './ProjectDashboard';
import { useRouter } from 'next/navigation';

type Props = {
  params: Promise<{ id: string }>;
  searchParams?: { [key: string]: string | string[] | undefined };
};

export default function ProjectDetailPage({ params: paramsPromise, searchParams }: Props) {
  const params = use(paramsPromise);
  const { id } = params;

  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isStartingTeam, setIsStartingTeam] = useState(false);
  const router = useRouter();
  
  useEffect(() => {
    fetchProjectData();
  }, [id]);
  
  const fetchProjectData = async () => {
    try {
      setLoading(true);
      
      // Fetch workspace details
      const workspaceData = await api.workspaces.get(id);
      setWorkspace(workspaceData);
      
      // Fetch agents
      const agentsData = await api.agents.list(id);
      setAgents(agentsData);
      
      setError(null);
    } catch (err) {
      console.error('Failed to fetch project data:', err);
      setError('Impossibile caricare i dati del progetto. Riprova più tardi.');
      
      // Mock data for testing
      setWorkspace({
        id: id,
        name: 'Progetto Marketing Digitale',
        description: 'Campagna di marketing sui social media',
        user_id: '123e4567-e89b-12d3-a456-426614174000',
        status: 'active',
        goal: 'Aumentare la visibilità del brand',
        budget: { max_amount: 1000, currency: 'EUR' },
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      });
      
      setAgents([
        {
          id: '1',
          workspace_id: id,
          name: 'Project Manager',
          role: 'Project Management',
          seniority: 'expert',
          description: 'Coordina l\'intero progetto',
          status: 'active',
          health: { status: 'healthy' },
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: '2',
          workspace_id: id,
          name: 'Content Specialist',
          role: 'Content Creation',
          seniority: 'senior',
          description: 'Crea contenuti di alta qualità',
          status: 'active',
          health: { status: 'healthy' },
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: '3',
          workspace_id: id,
          name: 'Data Analyst',
          role: 'Data Analysis',
          seniority: 'senior',
          description: 'Analizza e visualizza dati',
          status: 'active',
          health: { status: 'healthy' },
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };
  
  const handleStartTeam = async () => {
    if (!workspace) return;
    
    try {
      setIsStartingTeam(true);
      await api.monitoring.startTeam(workspace.id);
      
      setWorkspace(prev => prev ? { ...prev, status: 'active' } : null);
      setError(null);
      
      // Refresh the page after a short delay
      setTimeout(() => {
        window.location.reload();
      }, 1000);
      
    } catch (err) {
      console.error('Failed to start team:', err);
      setError('Impossibile avviare il team. Riprova più tardi.');
    } finally {
      setIsStartingTeam(false);
    }
  };
    
  const handleDeleteProject = async () => {
    if (!workspace) return;
    
    try {
      setIsDeleting(true);
      const success = await api.workspaces.delete(workspace.id);
      
      if (success) {
        router.push('/projects');
      } else {
        setError('Impossibile eliminare il progetto. Riprova più tardi.');
        setIsDeleteModalOpen(false);
      }
    } catch (err) {
      console.error('Failed to delete project:', err);
      setError(err instanceof Error ? err.message : 'Si è verificato un errore durante l\'eliminazione del progetto');
    } finally {
      setIsDeleting(false);
    }
  };
  
  return (
    <ProjectDashboard
      workspace={workspace}
      agents={agents}
      loading={loading}
      error={error}
      onStartTeam={handleStartTeam}
      onDeleteProject={handleDeleteProject}
      isStartingTeam={isStartingTeam}
      isDeleteModalOpen={isDeleteModalOpen}
      setIsDeleteModalOpen={setIsDeleteModalOpen}
    />
  );
}