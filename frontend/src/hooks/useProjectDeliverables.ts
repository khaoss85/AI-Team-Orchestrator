import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '@/utils/api';
import { ProjectDeliverablesExtended, ProjectOutputExtended, DeliverableFeedback } from '@/types';

export const useProjectDeliverables = (workspaceId: string) => {
  const [deliverables, setDeliverables] = useState<ProjectDeliverablesExtended | null>(null);
  const [finalDeliverables, setFinalDeliverables] = useState<ProjectOutputExtended[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const fetchTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastFetchRef = useRef<number>(0);
  const cacheRef = useRef<{ data: ProjectDeliverablesExtended | null; timestamp: number }>({ data: null, timestamp: 0 });
  
  const DEBOUNCE_DELAY = 500; // 500ms debounce
  const CACHE_DURATION = 30000; // 30 seconds cache

  const fetchDeliverables = useCallback(async (forceRefresh = false) => {
    // Check cache first (unless forced refresh)
    const now = Date.now();
    if (!forceRefresh && cacheRef.current.data && (now - cacheRef.current.timestamp) < CACHE_DURATION) {
      const cachedData = cacheRef.current.data;
      setDeliverables(cachedData);
      const finalDeliverablesData = cachedData.key_outputs.filter(output => 
        output.type === 'final_deliverable' || output.category === 'final_deliverable'
      );
      setFinalDeliverables(finalDeliverablesData);
      setLoading(false);
      return;
    }

    // Debounce API calls
    if (fetchTimeoutRef.current) {
      clearTimeout(fetchTimeoutRef.current);
    }
    
    // Rate limiting - prevent calls more frequent than every 100ms
    const timeSinceLastFetch = now - lastFetchRef.current;
    if (timeSinceLastFetch < 100) {
      return;
    }
    
    fetchTimeoutRef.current = setTimeout(async () => {
      try {
        setLoading(true);
        setError(null);
        lastFetchRef.current = Date.now();
        
        // Fetch completo dei deliverable
        const deliverablesData = await api.monitoring.getProjectDeliverables(workspaceId);
        
        // Update cache
        cacheRef.current = {
          data: deliverablesData,
          timestamp: Date.now()
        };
        
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
    }, forceRefresh ? 0 : DEBOUNCE_DELAY);
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
      // Force refresh cache after feedback submission
      await fetchDeliverables(true);
    },
    [workspaceId, fetchDeliverables],
  );

  useEffect(() => {
    if (workspaceId) {
      fetchDeliverables();
      
      // Set up auto-refresh interval
      const interval = setInterval(() => {
        fetchDeliverables(true); // Force refresh every 30 seconds
      }, 30000);
      
      return () => {
        clearInterval(interval);
        if (fetchTimeoutRef.current) {
          clearTimeout(fetchTimeoutRef.current);
        }
      };
    }
    
    // Cleanup timeout on unmount
    return () => {
      if (fetchTimeoutRef.current) {
        clearTimeout(fetchTimeoutRef.current);
      }
    };
  }, [workspaceId, fetchDeliverables]);

  return {
    deliverables,
    finalDeliverables,
    loading,
    error,
    refetch: () => fetchDeliverables(true), // Force refresh on manual refetch
    submitFeedback,
    checkForFinalDeliverables,
    hasFinalDeliverables: finalDeliverables.length > 0,
    finalDeliverablesCount: finalDeliverables.length
  };
};