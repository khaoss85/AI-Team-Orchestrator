export const transformTaskToEnhancedResult = (
  task: Task, 
  agents: Agent[]
): EnhancedProjectResult => {
  const agent = agents.find(a => a.id === task.agent_id);
  const content = extractTaskContent(task);
  
  const isFinalDeliverable = Boolean(
    task.context_data?.is_final_deliverable || 
    task.context_data?.deliverable_aggregation ||
    task.result?.type === 'final_deliverable'
  );
  
  return {
    id: task.id,
    title: task.name,
    description: task.description || 'Nessuna descrizione',
    date: new Date(task.updated_at).toLocaleDateString('it-IT'),
    type: isFinalDeliverable ? 'final_deliverable' : determineTaskType(task),
    icon: isFinalDeliverable ? '🎯' : getTaskIcon(task),
    creator: agent?.name || 'Sistema',
    isFinalDeliverable,
    completeness: calculateCompleteness(content),
    priority: isFinalDeliverable ? 1 : 2,
    content
  };
};

const extractTaskContent = (task: Task) => {
  if (!task.result) return getEmptyContent();
  
  try {
    const result = typeof task.result === 'string' ? JSON.parse(task.result) : task.result;
    
    // Per deliverable finali, prova a estrarre dati strutturati
    if (task.context_data?.is_final_deliverable || task.context_data?.deliverable_aggregation) {
      const detailedData = result.detailed_results_json 
        ? JSON.parse(result.detailed_results_json) 
        : result;
      
      return {
        summary: result.summary || result.executive_summary || '',
        keyPoints: result.key_points || [],
        details: result.details || result.full_output || JSON.stringify(result, null, 2),
        keyInsights: detailedData.key_findings || detailedData.key_insights || [],
        metrics: detailedData.project_metrics || detailedData.metrics || {},
        recommendations: detailedData.recommendations || detailedData.final_recommendations || [],
        nextSteps: detailedData.next_steps || detailedData.action_items || []
      };
    }
    
    // Per task normali
    return {
      summary: result.summary || result.output || 'Risultato completato',
      keyPoints: result.key_points || result.insights || [],
      details: result.details || JSON.stringify(result, null, 2),
      keyInsights: [],
      metrics: {},
      recommendations: [],
      nextSteps: []
    };
  } catch (e) {
    console.warn('Error parsing task result:', e);
    return getEmptyContent();
  }
};

const getEmptyContent = () => ({
  summary: 'Nessun risultato disponibile',
  keyPoints: [],
  details: '',
  keyInsights: [],
  metrics: {},
  recommendations: [],
  nextSteps: []
});

const calculateCompleteness = (content: any): number => {
  let score = 0;
  if (content.summary) score += 20;
  if (content.keyPoints.length > 0) score += 20;
  if (content.keyInsights.length > 0) score += 25;
  if (Object.keys(content.metrics).length > 0) score += 20;
  if (content.recommendations.length > 0) score += 15;
  return Math.min(100, score);
};
