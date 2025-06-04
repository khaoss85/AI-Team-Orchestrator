import { useState, useEffect, useCallback } from 'react';
import { api } from '@/utils/api';
import { ProjectDeliverablesExtended, ProjectOutputExtended, DeliverableFeedback } from '@/types';

export const useProjectDeliverables = (workspaceId: string) => {
  const [deliverables, setDeliverables] = useState<ProjectDeliverablesExtended | null>(null);
  const [finalDeliverables, setFinalDeliverables] = useState<ProjectOutputExtended[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDeliverables = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch completo dei deliverable
      const deliverablesData = await api.monitoring.getProjectDeliverables(workspaceId);
      setDeliverables(deliverablesData);
      
      // Estrai deliverable finali
      const finalDeliverablesData = deliverablesData.key_outputs.filter(output => 
        output.type === 'final_deliverable' || output.category === 'final_deliverable'
      );
      setFinalDeliverables(finalDeliverablesData);
      
    } catch (err) {
      console.error('Error fetching deliverables:', err);
      setError(err instanceof Error ? err.message : 'Errore nel caricamento deliverable');
    } finally {
      setLoading(false);
    }
  }, [workspaceId]);

  const checkForFinalDeliverables = useCallback(async () => {
    try {
      const status = await api.monitoring.checkFinalDeliverablesStatus(workspaceId);
      setFinalDeliverables(status.deliverables);
      return status;
    } catch (err) {
      console.error('Error checking final deliverables:', err);
      return { hasFinalDeliverables: false, count: 0, deliverables: [] };
    }
  }, [workspaceId]);

  const submitFeedback = useCallback(
    async (feedback: DeliverableFeedback) => {
      await api.monitoring.submitDeliverableFeedback(workspaceId, feedback);
      await fetchDeliverables();
    },
    [workspaceId, fetchDeliverables],
  );

  useEffect(() => {
    if (workspaceId) {
      fetchDeliverables();
    }
  }, [workspaceId, fetchDeliverables]);

  return {
    deliverables,
    finalDeliverables,
    loading,
    error,
    refetch: fetchDeliverables,
    submitFeedback,
    checkForFinalDeliverables,
    hasFinalDeliverables: finalDeliverables.length > 0,
    finalDeliverablesCount: finalDeliverables.length
  };
};