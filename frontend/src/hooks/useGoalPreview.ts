import { useState, useCallback } from 'react';

// Get API base URL function (copied from api.ts)
const getApiBaseUrl = () => {
  if (typeof window !== 'undefined') {
    // Se siamo in localhost, punta a localhost:8000 (main server)
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      return 'http://localhost:8000';
    }
  }
  
  // Altrimenti usa la variabile d'ambiente
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
};

interface ExtractedGoal {
  id: string;
  value: number;
  unit: string;
  type: string;
  description: string;
  confidence: number;
  editable: boolean;
}

interface GoalPreviewResponse {
  success: boolean;
  original_goal: string;
  extracted_goals: ExtractedGoal[];
  message: string;
}

// Simple toast notification function
const showToast = (message: { title: string; description?: string; variant?: 'default' | 'destructive' }) => {
  // In a real app, you would use a proper toast library
  // For now, we'll use console.log and alert for errors
  if (message.variant === 'destructive') {
    console.error(`${message.title}: ${message.description}`);
    alert(`${message.title}: ${message.description}`);
  } else {
    console.log(`${message.title}: ${message.description}`);
  }
};

export function useGoalPreview(workspaceId: string) {
  const [isLoading, setIsLoading] = useState(false);
  const [extractedGoals, setExtractedGoals] = useState<ExtractedGoal[]>([]);
  const [originalGoal, setOriginalGoal] = useState<string>('');
  const toast = showToast;

  const previewGoals = useCallback(async (goalText: string) => {
    if (!goalText.trim()) {
      toast({
        title: 'Errore',
        description: 'Inserisci un obiettivo da analizzare',
        variant: 'destructive',
      });
      return false;
    }

    setIsLoading(true);
    setOriginalGoal(goalText);

    try {
      const apiBaseUrl = getApiBaseUrl();
      const url = `${apiBaseUrl}/api/workspaces/${workspaceId}/goals/preview`;
      
      console.log('🚀 Sending goal preview request:', {
        url,
        goal: goalText
      });

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ goal: goalText }),
      });

      console.log('📡 Response status:', response.status);
      console.log('📡 Response headers:', Object.fromEntries(response.headers));

      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ Error response:', errorText);
        
        // Fallback mock data for testing UI
        if (response.status === 404 || response.status === 500) {
          console.log('🔄 Using mock data for UI testing');
          const mockData: GoalPreviewResponse = {
            success: true,
            original_goal: goalText,
            extracted_goals: [
              {
                id: 'preview_0',
                value: 50,
                unit: 'contatti ICP',
                type: 'deliverables',
                description: 'Raccogliere 50 contatti qualificati',
                confidence: 0.95,
                editable: true
              },
              {
                id: 'preview_1',
                value: 3,
                unit: 'sequenze email',
                type: 'deliverables', 
                description: 'Creare 3 sequenze email',
                confidence: 0.95,
                editable: true
              }
            ],
            message: 'Ho identificato 2 obiettivi (usando dati mock)'
          };
          
          setExtractedGoals(mockData.extracted_goals);
          toast({
            title: 'Obiettivi Identificati (Mock)',
            description: mockData.message,
          });
          return true;
        }
        
        throw new Error(`Failed to preview goals: ${response.status} ${errorText}`);
      }

      const data: GoalPreviewResponse = await response.json();
      
      if (data.success && data.extracted_goals.length > 0) {
        setExtractedGoals(data.extracted_goals);
        toast({
          title: 'Obiettivi Identificati',
          description: data.message,
        });
        return true;
      } else {
        toast({
          title: 'Nessun obiettivo trovato',
          description: 'Prova a riformulare il tuo obiettivo in modo più specifico',
          variant: 'destructive',
        });
        return false;
      }
    } catch (error) {
      console.error('Error previewing goals:', error);
      toast({
        title: 'Errore',
        description: 'Impossibile analizzare l\'obiettivo. Riprova più tardi.',
        variant: 'destructive',
      });
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [workspaceId, toast]);

  const confirmGoals = useCallback(async (goals: ExtractedGoal[]) => {
    setIsLoading(true);

    try {
      const apiBaseUrl = getApiBaseUrl();
      const url = `${apiBaseUrl}/api/workspaces/${workspaceId}/goals/confirm`;
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ goals }),
      });

      if (!response.ok) {
        // Mock success for UI testing when backend is not available
        if (response.status === 404 || response.status === 500) {
          console.log('🔄 Using mock confirmation for UI testing');
          toast({
            title: 'Obiettivi Confermati (Mock)',
            description: `✅ ${goals.length} obiettivi confermati per testing`,
          });
          return true;
        }
        throw new Error('Failed to confirm goals');
      }

      const data = await response.json();
      
      if (data.success) {
        toast({
          title: 'Obiettivi Confermati',
          description: data.message,
        });
        return true;
      }
      return false;
    } catch (error) {
      console.error('Error confirming goals:', error);
      
      // Mock success for network errors when testing UI
      if (error instanceof TypeError && error.message.includes('fetch')) {
        console.log('🔄 Network error, using mock confirmation for UI testing');
        toast({
          title: 'Obiettivi Confermati (Mock)',
          description: `✅ ${goals.length} obiettivi confermati per testing`,
        });
        return true;
      }
      
      toast({
        title: 'Errore',
        description: 'Impossibile salvare gli obiettivi. Riprova.',
        variant: 'destructive',
      });
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [workspaceId, toast]);

  const editGoal = useCallback((index: number, updatedGoal: ExtractedGoal) => {
    setExtractedGoals(prev => {
      const newGoals = [...prev];
      newGoals[index] = updatedGoal;
      return newGoals;
    });
  }, []);

  const removeGoal = useCallback((index: number) => {
    setExtractedGoals(prev => prev.filter((_, i) => i !== index));
    toast({
      title: 'Obiettivo rimosso',
      description: 'L\'obiettivo è stato rimosso dalla lista',
    });
  }, [toast]);

  const reset = useCallback(() => {
    setExtractedGoals([]);
    setOriginalGoal('');
  }, []);

  return {
    isLoading,
    extractedGoals,
    originalGoal,
    previewGoals,
    confirmGoals,
    editGoal,
    removeGoal,
    reset,
  };
}