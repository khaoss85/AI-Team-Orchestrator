'use client';

import React, { useState, useEffect, use } from 'react'; // Import 'use' from React
import { useRouter } from 'next/navigation';
import { api } from '@/utils/api';
import { Workspace, DirectorTeamProposal, AgentSeniority } from '@/types';
import TeamExplanationAnimation from '@/components/TeamExplanationAnimation';
import { GoalConfirmation } from '@/components/orchestration/GoalConfirmation';
import { useGoalPreview } from '@/hooks/useGoalPreview';
import { ProgressIndicator } from '@/components/ui/ProgressIndicator';


type Props = {
  params: Promise<{ id: string }>;
};

export default function ConfigureProjectPage({ params: paramsPromise }: Props) {
  // Use React.use() to "unlock" the parameters Promise
  const params = use(paramsPromise);
  const { id } = params; // Now 'id' is accessible from the resolved params object

  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [proposalLoading, setProposalLoading] = useState(false);
  const [proposalId, setProposalId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [proposal, setProposal] = useState<DirectorTeamProposal | null>(null);
  const [userFeedback, setUserFeedback] = useState<string>('');
  const [showFeedbackInput, setShowFeedbackInput] = useState<boolean>(false);
  const [goalsConfirmed, setGoalsConfirmed] = useState(false);
  
  // Progress tracking state
  const [progressState, setProgressState] = useState({
    progress: 0,
    message: 'Initializing...',
    status: 'analyzing'
  });

  const mockUserId = '123e4567-e89b-12d3-a456-426614174000';
  
  // Hook for goal preview functionality
  const {
    isLoading: goalPreviewLoading,
    extractedGoals,
    finalMetrics,
    strategicDeliverables,
    goalSummary,
    originalGoal,
    progressStatus,
    showProgress,
    previewGoals,
    confirmGoals,
    editGoal,
    removeGoal,
    reset: resetGoals,
    startProgressMonitoring,
    setExtractedGoals,
    setOriginalGoal,
  } = useGoalPreview(id);

  useEffect(() => {
    const fetchWorkspace = async () => {
      try {
        setLoading(true);
        // Use resolved 'id'
        const data = await api.workspaces.get(id);
        setWorkspace(data);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch workspace:', err);
        setError('Unable to load project details. Please try again later.');
        setWorkspace({
          id: id, // Use resolved 'id'
          name: 'Digital Marketing Project',
          description: 'Social media marketing campaign',
          user_id: mockUserId,
          status: 'created',
          goal: 'Increase brand visibility',
          budget: { max_amount: 1000, currency: 'EUR' },
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        });
      } finally {
        setLoading(false);
      }
    };

    if (id) { // Check resolved 'id' before fetching
      fetchWorkspace();
    }
  }, [id]); // Use resolved 'id' as dependency

  // Progress monitoring is now handled by useGoalPreview hook

  // Handle goal preview when workspace has a goal
  useEffect(() => {
    const checkExistingGoalsAndStart = async () => {
      console.log('🔍 Goal effect triggered:', {
        hasGoal: !!workspace?.goal,
        goalsConfirmed,
        extractedGoalsCount: extractedGoals.length,
        workspaceId: workspace?.id
      });
      
      if (workspace?.goal && !goalsConfirmed && extractedGoals.length === 0) {
        // First check if goals already exist from previous analysis
        try {
          console.log('🔍 Checking for existing goals...');
          const response = await api.workspaces.getGoals(workspace.id);
          
          if (response && response.success && response.goals && response.goals.length > 0) {
            // Goals already exist, convert them to the format expected by GoalConfirmation
            console.log('✅ Found existing goals, loading them directly');
            
            const convertedGoals = response.goals.map((goal: any, index: number) => ({
              id: `existing_${index}`,
              value: goal.target_value,
              unit: goal.unit,
              type: goal.metric_type,
              description: goal.description,
              confidence: goal.confidence || 0.9,
              editable: true,
              // Preserve strategic deliverable data if available
              deliverable_type: goal.semantic_context?.deliverable_type,
              business_value: goal.semantic_context?.business_value,
              acceptance_criteria: goal.semantic_context?.acceptance_criteria,
              execution_phase: goal.semantic_context?.execution_phase,
              autonomy_level: goal.semantic_context?.autonomy_level,
              autonomy_reason: goal.semantic_context?.autonomy_reason,
              available_tools: goal.semantic_context?.available_tools,
              human_input_required: goal.semantic_context?.human_input_required,
              semantic_context: goal.semantic_context
            }));
            
            // Set goals directly without progress monitoring
            setExtractedGoals(convertedGoals);
            setOriginalGoal(workspace.goal);
            console.log('✅ Existing goals loaded, ready for confirmation');
            return;
          }
        } catch (error) {
          console.log('⚠️ No existing goals found or API error, starting fresh analysis');
        }

        // No existing goals, start fresh goal extraction
        console.log('🔄 Starting fresh goal extraction and preview process');
        console.log('📝 Goal text to extract:', workspace.goal);
        const cleanup = startProgressMonitoring();
        const previewResult = await previewGoals(workspace.goal);
        console.log('📊 Preview result:', previewResult);
        
        return cleanup;
      }
    };
    
    checkExistingGoalsAndStart();
  }, [workspace?.goal, workspace?.id, goalsConfirmed, extractedGoals.length, previewGoals, startProgressMonitoring]);

  const handleConfirmGoals = async (goals: any[]) => {
    const success = await confirmGoals(goals);
    if (success) {
      setGoalsConfirmed(true);
    }
  };

  const handleReprocessGoals = async () => {
    if (workspace?.goal) {
      resetGoals();
      // Reset progress state and start monitoring
      setProgressState({ progress: 0, message: 'Initializing...', status: 'analyzing' });
      await previewGoals(workspace.goal);
    }
  };

  const handleCreateProposal = async () => {
    if (!workspace || !goalsConfirmed) return;

    try {
      setProposalLoading(true);
      setError(null);

      // Build enhanced goal description with extracted goals
      const enhancedGoalDescription = (() => {
        if (!extractedGoals.length) {
          return workspace.goal || 'Complete the project successfully';
        }
        
        const goalsSummary = extractedGoals.map(goal => 
          `${goal.description} (${goal.value} ${goal.unit})`
        ).join(', ');
        
        return `${workspace.goal}\n\nSpecific Objectives: ${goalsSummary}`;
      })();

      const directorConfig = {
        workspace_id: workspace.id,
        goal: enhancedGoalDescription,
        budget_constraint: workspace.budget || { max_amount: 1000, currency: 'EUR' },
        user_id: workspace.user_id,
        user_feedback: userFeedback || undefined,
        // Include extracted goals for Enhanced Director
        extracted_goals: extractedGoals.length > 0 ? extractedGoals : undefined
      };

      console.log('🚀 Creating proposal with config:', directorConfig);

      // Add timeout to API call
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('Timeout: The Director is taking too long')), 120000); // 2 minutes
      });

      const apiPromise = api.director.createProposal(directorConfig);
      
      const data = await Promise.race([apiPromise, timeoutPromise]) as DirectorTeamProposal;
      
      console.log('✅ Received proposal data:', data);
      
      setProposal(data);
      if (data.id) {
        setProposalId(data.id);
      }
      setUserFeedback('');
      setShowFeedbackInput(false);
    } catch (err: any) {
      console.error('❌ Failed to create team proposal:', err);
      
      if (err.message.includes('Timeout')) {
        setError('The Director is still processing. Try reloading the page in a few seconds.');
      } else {
        setError(`Error generating proposal: ${err.message || 'Unknown error'}`);
      }

      // Fallback proposal only if it's not a timeout
      if (!err.message.includes('Timeout') && workspace) {
        setProposal({
          workspace_id: workspace.id,
          agents: [
            {
              workspace_id: workspace.id,
              name: "Project Manager",
              role: "Project Management",
              seniority: "expert" as AgentSeniority,
              description: "Coordinates the entire project and manages handoffs between agents",
              system_prompt: "You are an expert project manager who coordinates a team of specialized agents."
            },
            {
              workspace_id: workspace.id,
              name: "Content Specialist",
              role: "Content Creation",
              seniority: "senior" as AgentSeniority,
              description: "Specialist in creating high-quality content",
              system_prompt: "You are a specialist in creating engaging marketing content."
            },
            {
              workspace_id: workspace.id,
              name: "Data Analyst",
              role: "Data Analysis",
              seniority: "senior" as AgentSeniority,
              description: "Analyzes data and creates informative visualizations",
              system_prompt: "You are a data analyst specialized in data interpretation and visualization."
            }
          ],
          handoffs: [
            {
              source_agent_id: "00000000-0000-0000-0000-000000000000",
              target_agent_id: "00000000-0000-0000-0000-000000000000",
              description: "Handoff of analysis results for content creation"
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
          rationale: "Team designed to balance skills and budget constraints. The expert PM will ensure efficient management, while senior specialists will provide high-quality results at a reasonable cost."
        });
      }
    } finally {
      setProposalLoading(false);
    }
  };

  const handleApproveProposal = async () => {
    if (!workspace || !proposalId) return;

    try {
      setLoading(true);
      setError(null);

      // Create timeout promise for approval API call
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('APPROVAL_TIMEOUT')), 15000); // 15 seconds timeout
      });

      const approvalPromise = api.director.approveProposal(workspace.id, proposalId);
      
      // Race between API call and timeout
      await Promise.race([approvalPromise, timeoutPromise]);

      // If we get here, approval was successful
      console.log('✅ Team approved successfully, redirecting...');
      router.push(`/projects/${workspace.id}`);
      
    } catch (err: any) {
      console.error('Failed to approve team proposal:', err);
      
      if (err.message === 'APPROVAL_TIMEOUT') {
        // Timeout case - team is likely being created in background
        setError('The team is still being created in the background. We\'re redirecting you to the project...');
        console.log('⏰ Approval timed out, but team creation likely started - redirecting anyway');
      } else {
        setError('Unable to approve the team proposal. The process might still be in progress...');
      }

      // Always redirect after a short delay, regardless of error type
      // The team creation process likely started even if the API didn't respond in time
      setTimeout(() => {
        console.log('🔄 Redirecting to project page...');
        router.push(`/projects/${workspace.id}`);
      }, 2000); // 2 second delay to show the message
      
    } finally {
      // Don't reset loading immediately - wait for redirect
      setTimeout(() => {
        setLoading(false);
      }, 2100);
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

  const formatAgentName = (name: string) => {
    // Handle names like "ElenaRossi" -> "Elena Rossi"
    if (name && typeof name === 'string') {
      // Add space before uppercase letters that follow lowercase letters
      return name.replace(/([a-z])([A-Z])/g, '$1 $2');
    }
    return name;
  };

  if (loading && !workspace) {
    return (
      <div className="container mx-auto max-w-4xl">
        <div className="text-center py-10">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-indigo-600 border-r-transparent"></div>
          <p className="mt-2 text-gray-600">Loading project...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-4xl">
      <h1 className="text-2xl font-semibold mb-1">
        {!goalsConfirmed ? 'Confirm Project Objectives' : 'Configure Agent Team'}
      </h1>
      <p className="text-gray-600 mb-6">
        {!goalsConfirmed 
          ? "The AI has analyzed your objective using strategic decomposition. Confirm or modify the targets before proceeding."
          : "The virtual director will propose an optimal agent team to achieve your objectives."
        }
      </p>

      {error && (
        <div className="bg-red-50 text-red-700 p-4 rounded-md mb-6">
          {error}
        </div>
      )}

      {workspace && (
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Project Details</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <p className="text-sm text-gray-500">Name</p>
              <p className="font-medium">{workspace.name}</p>
            </div>

            <div>
              <p className="text-sm text-gray-500">Status</p>
              <p className="font-medium">
                <span className={`inline-block px-2 py-1 text-xs rounded-full ${
                  workspace.status === 'active' ? 'bg-green-100 text-green-800' :
                  workspace.status === 'created' ? 'bg-blue-100 text-blue-800' :
                  workspace.status === 'paused' ? 'bg-yellow-100 text-yellow-800' :
                  workspace.status === 'completed' ? 'bg-gray-100 text-gray-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {workspace.status === 'active' ? 'Active' :
                  workspace.status === 'created' ? 'Created' :
                  workspace.status === 'paused' ? 'Paused' :
                  workspace.status === 'completed' ? 'Completed' :
                  'Error'}
                </span>
              </p>
            </div>

            <div>
              <p className="text-sm text-gray-500">Objective</p>
              <p className="font-medium">{workspace.goal || 'Not specified'}</p>
            </div>

            <div>
              <p className="text-sm text-gray-500">Budget</p>
              <p className="font-medium">
                {workspace.budget
                  ? `${workspace.budget.max_amount} ${workspace.budget.currency}`
                  : 'Not specified'}
              </p>
            </div>
          </div>

        </div>
      )}

      {/* Progress Indicator during goal analysis */}
      {workspace && goalPreviewLoading && extractedGoals.length === 0 && (
        <div className="mb-6">
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-lg font-semibold mb-4 text-center">AI Objective Analysis</h2>
            <p className="text-gray-600 mb-6 text-center">
              Our AI is analyzing your objective to create a detailed plan and identify strategic deliverables.
            </p>
            <ProgressIndicator
              progress={progressState.progress}
              message={progressState.message}
              status={progressState.status}
              className="mb-4"
            />
            <div className="text-sm text-gray-500 text-center mt-4">
              This process may take a few seconds to ensure accurate analysis.
            </div>
          </div>
        </div>
      )}

      {/* Goal Confirmation Section */}
      {workspace && extractedGoals.length > 0 && !goalsConfirmed && (
        <div className="mb-6">
          <GoalConfirmation
            goals={extractedGoals}
            finalMetrics={finalMetrics}
            strategicDeliverables={strategicDeliverables}
            goalSummary={goalSummary}
            originalGoal={originalGoal}
            onConfirm={handleConfirmGoals}
            onEdit={editGoal}
            onRemove={removeGoal}
            onReprocess={handleReprocessGoals}
            isLoading={goalPreviewLoading}
          />
        </div>
      )}

      {/* Show proposal generation button only after goals are confirmed */}
      {workspace && goalsConfirmed && !proposal && (
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h2 className="text-lg font-semibold mb-2">Generate Agent Team</h2>
          <p className="text-gray-600 mb-4">
            Now that the objectives are confirmed, we can proceed to create the perfect team to achieve them.
          </p>
          <button
            onClick={handleCreateProposal}
            className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition-colors duration-150 flex items-center"
            disabled={proposalLoading}
          >
            {proposalLoading ? (
              <>
                <div className="h-4 w-4 border-2 border-white border-r-transparent rounded-full animate-spin mr-2"></div>
                Generating proposal...
              </>
            ) : (
              'Generate Team Proposal'
            )}
          </button>
          <p className="mt-2 text-xs text-gray-500">
            The director will analyze the confirmed objectives and propose an optimal agent team.
          </p>
        </div>
      )}
          
    {/* 🎯 ADD HERE - Team Explanation Animation */}
      {proposalLoading && (
        <div className="mb-6">
          <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
            <div className="flex items-center justify-center mb-4">
              <div className="h-4 w-4 border-2 border-indigo-600 border-r-transparent rounded-full animate-spin mr-3"></div>
              <h2 className="text-lg font-semibold text-gray-900">
                The Director is analyzing the project...
              </h2>
            </div>
            <p className="text-center text-gray-600 mb-6">
              We're creating the perfect team for your objectives. In the meantime, discover how our system works:
            </p>
          </div>
          <TeamExplanationAnimation />
        </div>
      )}

{proposal && (
  <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
    <h2 className="text-lg font-semibold mb-2">Team Proposal</h2>
    <p className="text-gray-600 mb-4">{proposal.rationale}</p>

    <div className="mb-6">
      <h3 className="text-md font-medium mb-2">Estimated Cost</h3>
      <div className="bg-gray-50 p-4 rounded-md">
        <div className="flex justify-between items-center mb-2">
          <span className="text-gray-600">Total Cost:</span>
          <span className="font-semibold">
            {proposal.estimated_cost.total || proposal.estimated_cost.total_estimated_cost || 0} EUR
          </span>
        </div>

        {/* Supports both breakdown formats */}
        {((proposal.estimated_cost.breakdown_by_agent && Object.keys(proposal.estimated_cost.breakdown_by_agent).length > 0) ||
          (proposal.estimated_cost.breakdown && Object.keys(proposal.estimated_cost.breakdown).length > 0)) && (
          <div className="text-sm text-gray-600">
            <div className="mt-2 mb-1">Cost breakdown:</div>
            <ul className="space-y-1">
              {Object.entries(
                proposal.estimated_cost.breakdown_by_agent || 
                proposal.estimated_cost.breakdown || 
                {}
              ).map(([role, cost]) => (
                <li key={role} className="flex justify-between">
                  <span>{role}:</span>
                  <span>{cost} EUR</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>

          <h3 className="text-md font-medium mb-3">Proposed Agents</h3>
          
          {/* Team Composition Overview */}
          {proposal.agents?.length > 0 && (
            <div className="flex items-center gap-4 mb-4 p-3 bg-gray-50 rounded-md">
              <div className="text-sm text-gray-600">
                <span className="font-medium text-gray-900">{proposal.agents?.length || 0}</span> agents
              </div>
              <div className="text-sm text-gray-600">
                <span className="font-medium text-gray-900">
                  {proposal.agents?.filter(a => a.seniority === 'expert').length || 0}
                </span> expert
              </div>
              <div className="text-sm text-gray-600">
                <span className="font-medium text-gray-900">
                  {proposal.agents?.filter(a => a.seniority === 'senior').length || 0}
                </span> senior
              </div>
              <div className="text-sm text-gray-600">
                <span className="font-medium text-gray-900">
                  {proposal.agents?.filter(a => a.seniority === 'junior').length || 0}
                </span> junior
              </div>
            </div>
          )}
          
          <div className="space-y-4 mb-6">
            {proposal.agents?.length > 0 ? proposal.agents.map((agent, index) => (
              <div key={index} className="border border-gray-200 rounded-md p-4 hover:border-gray-300 transition-colors">
                <div className="flex justify-between items-start mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-semibold text-base text-gray-900">{formatAgentName(agent.name)}</h4>
                      <span className={`text-xs px-2 py-1 rounded-full ${getSeniorityColor(agent.seniority)}`}>
                        {getSeniorityLabel(agent.seniority)}
                      </span>
                    </div>
                    <p className="text-sm font-medium text-indigo-600 mb-2">{agent.role}</p>
                    <p className="text-sm text-gray-600 leading-relaxed">{agent.description}</p>
                  </div>
                </div>
              </div>
            )) : (
              <div className="text-center text-gray-500 py-4">
                <p>No agents available in the proposal</p>
              </div>
            )}
          </div>

<div className="flex justify-end space-x-3">
  {proposal && (
    <>
      {showFeedbackInput ? (
        <div className="w-full mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Feedback to improve the next proposal
          </label>
          <textarea
            value={userFeedback}
            onChange={(e) => setUserFeedback(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            rows={3}
            placeholder="E.g. 'I'd like a smaller team', 'Need an SEO expert', 'Reduce costs', etc."
          />
          <div className="flex justify-end mt-2">
            <button
              onClick={() => setShowFeedbackInput(false)}
              className="px-3 py-1 bg-gray-100 text-gray-700 rounded-md text-sm hover:bg-gray-200 transition mr-2"
            >
              Cancel
            </button>
            <button
              onClick={handleCreateProposal}
              className="px-3 py-1 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition"
              disabled={proposalLoading}
            >
              {proposalLoading ? "Generating..." : "Generate with feedback"}
            </button>
          </div>
        </div>
      ) : (
        <button
          onClick={() => setShowFeedbackInput(true)}
          className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md text-sm hover:bg-gray-200 transition"
          disabled={loading}
        >
          Regenerate with feedback
        </button>
      )}
      <button
        onClick={() => {
          setUserFeedback('');
          setShowFeedbackInput(false);
          handleCreateProposal();
        }}
        className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md text-sm hover:bg-gray-200 transition"
        disabled={loading || proposalLoading}
      >
        Regenerate proposal
      </button>
    </>
  )}
    {proposal && proposal.user_feedback && (
  <div className="bg-blue-50 p-4 rounded-md mb-4">
    <h3 className="text-md font-medium mb-1">Feedback considered</h3>
    <p className="text-gray-600 text-sm">{proposal.user_feedback}</p>
  </div>
)}
  {!proposal && (
    <button
      onClick={handleCreateProposal}
      className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition-colors duration-150 flex items-center"
      disabled={proposalLoading}
    >
      {proposalLoading ? (
        <>
          <div className="h-4 w-4 border-2 border-white border-r-transparent rounded-full animate-spin mr-2"></div>
          Generating proposal...
        </>
      ) : (
        'Generate Team Proposal'
      )}
    </button>
  )}
  <button
    onClick={handleApproveProposal}
    className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition-colors duration-150 flex items-center"
    disabled={loading || !proposal}
  >
    {loading ? (
      <>
        <div className="h-4 w-4 border-2 border-white border-r-transparent rounded-full animate-spin mr-2"></div>
        Approval in progress...
      </>
    ) : (
      'Approve and Create Team'
    )}
  </button>
</div>
        </div>
      )}
    </div>
  );
}