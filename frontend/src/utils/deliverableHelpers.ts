import { Task, Agent } from '@/types'; // Assuming these types are correctly defined

export interface EnhancedProjectResult {
  id: string;
  title: string;
  description: string;
  date: string;
  type: string; // Consider using a more specific enum if possible
  icon: string;
  creator: string;
  isFinalDeliverable: boolean;
  completeness: number;
  priority: number;
  content: any; // Define a more specific type for content if possible
}

const determineTaskType = (task: Task): string => {
  const name = (task.name || '').toLowerCase();
  const description = (task.description || '').toLowerCase();
  const content = name + ' ' + description; // Combine name and description for keyword search

  if (content.includes('analis') || content.includes('ricerca') || content.includes('studio')) return 'analysis';
  if (content.includes('piano') || content.includes('strategi') || content.includes('progetta')) return 'strategy';
  if (content.includes('document') || content.includes('report') || content.includes('scrivi')) return 'document';
  // Add more specific keywords if needed for other types
  return 'general';
};

const getTaskIcon = (task: Task): string => {
  const type = determineTaskType(task); // Uses the function now defined in this file
  switch(type) {
    case 'analysis': return '🔍';
    case 'strategy': return '📈';
    case 'document': return '📄';
    default: return '📋';
  }
};

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
    type: isFinalDeliverable ? 'final_deliverable' : determineTaskType(task), // Now correctly calls the local function
    icon: isFinalDeliverable ? '🎯' : getTaskIcon(task), // Now correctly calls the local function
    creator: agent?.name || 'Sistema',
    isFinalDeliverable,
    completeness: calculateCompleteness(content),
    priority: isFinalDeliverable ? 1 : 2, // Prioritize final deliverables
    content
  };
};

// Make sure extractTaskContent, getEmptyContent, and calculateCompleteness are also defined in this file
const extractTaskContent = (task: Task) => {
  if (!task.result) return getEmptyContent();

  try {
    const result = typeof task.result === 'string' ? JSON.parse(task.result) : task.result;

    // For final deliverables, try to extract structured data
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

    // For normal tasks
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
  if (content.keyPoints && content.keyPoints.length > 0) score += 20; // Added check for existence
  if (content.keyInsights && content.keyInsights.length > 0) score += 25; // Added check for existence
  if (content.metrics && Object.keys(content.metrics).length > 0) score += 20; // Added check for existence
  if (content.recommendations && content.recommendations.length > 0) score += 15; // Added check for existence
  return Math.min(100, score);
};