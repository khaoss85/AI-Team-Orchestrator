'use client'
import React, { useState, useEffect } from 'react'
import type { Workspace, AssetCompletionStats } from '@/types'
import { api } from '@/utils/api'

interface Props {
  workspace: Workspace
  assetStats: AssetCompletionStats
  finalDeliverables: number
  completionPercentage?: number
  finalizationStatus?: any
}

interface WorkspaceGoal {
  id: string;
  metric_type: string;
  target_value: number;
  current_value: number;
  unit: string;
  status: string;
  completion_pct?: number;
}

interface GoalValidation {
  overall_achievement: number;
  validation_status: string;
  critical_issues: number;
}

const gradients = [
  'from-violet-600 via-purple-600 to-indigo-600',
  'from-emerald-500 via-teal-500 to-cyan-500',
  'from-pink-500 via-rose-500 to-red-500',
  'from-amber-500 via-orange-500 to-red-500',
  'from-blue-600 via-indigo-600 to-purple-600'
]

const ActionableHeroSection: React.FC<Props> = ({ workspace, assetStats, finalDeliverables, completionPercentage = 0, finalizationStatus }) => {
  const [goals, setGoals] = useState<WorkspaceGoal[]>([]);
  const [goalValidation, setGoalValidation] = useState<GoalValidation | null>(null);
  const [loadingGoals, setLoadingGoals] = useState(true);

  const gradient = React.useMemo(() => {
    const idx = workspace.id
      ? workspace.id.charCodeAt(0) % gradients.length
      : 0
    return gradients[idx]
  }, [workspace.id])

  // Fetch workspace goals
  useEffect(() => {
    const fetchGoals = async () => {
      if (!workspace.id) return;
      
      try {
        setLoadingGoals(true);
        
        // Fetch goals
        const goalsResponse = await api.workspaceGoals.getAll(workspace.id, { status: 'active' });
        if (goalsResponse.success) {
          const goalsWithProgress = goalsResponse.goals.map((goal: any) => ({
            ...goal,
            completion_pct: goal.target_value > 0 ? (goal.current_value / goal.target_value * 100) : 0
          }));
          setGoals(goalsWithProgress);
        }

        // Fetch goal validation
        try {
          const validationResponse = await api.goalValidation.validateWorkspace(workspace.id);
          if (validationResponse.validation_results) {
            const validations = validationResponse.validation_results;
            const avgAchievement = validations.reduce((sum: number, v: any) => 
              sum + (v.achievement_percentage || 0), 0) / validations.length;
            
            const criticalCount = validations.filter((v: any) => 
              v.severity === 'critical').length;

            setGoalValidation({
              overall_achievement: avgAchievement,
              validation_status: avgAchievement >= 85 ? 'excellent' : avgAchievement >= 60 ? 'good' : 'needs_improvement',
              critical_issues: criticalCount
            });
          }
        } catch (validationError) {
          console.warn('Goal validation not available:', validationError);
        }

      } catch (error) {
        console.error('Error fetching goals:', error);
      } finally {
        setLoadingGoals(false);
      }
    };

    fetchGoals();
  }, [workspace.id])

  // Calculate business value metrics
  const actualCompletionRate = completionPercentage > 0 ? completionPercentage : assetStats.completionRate
  const isProjectComplete = actualCompletionRate >= 80
  const businessValue = React.useMemo(() => {
    // Estimate business value based on completed assets
    const baseValue = assetStats.completedAssets * 2500 // €2,500 per asset
    const bonusValue = finalDeliverables * 3500 // €3,500 per final deliverable
    return baseValue + bonusValue
  }, [assetStats.completedAssets, finalDeliverables])

  const getStatusMessage = () => {
    if (isProjectComplete) {
      return {
        emoji: "🎉",
        title: "All deliverables completed successfully!",
        subtitle: `Your team of AI agents has produced ${assetStats.completedAssets} business-ready assets worth €${businessValue.toLocaleString()}. Ready to deploy immediately.`
      }
    } else if (actualCompletionRate >= 50) {
      return {
        emoji: "🚀",
        title: "Great progress! Almost there!",
        subtitle: `${assetStats.completedAssets} assets completed out of ${assetStats.totalAssets}. Estimated value: €${businessValue.toLocaleString()}.`
      }
    } else {
      return {
        emoji: "⚡",
        title: "AI team is working hard!",
        subtitle: `${assetStats.completedAssets} assets ready, ${assetStats.totalAssets - assetStats.completedAssets} in progress. Building your €${businessValue.toLocaleString()} solution.`
      }
    }
  }

  const status = getStatusMessage()

  return (
    <div className={`relative rounded-xl shadow-2xl p-8 text-white bg-gradient-to-br ${gradient} overflow-hidden`}>
      {/* Animated background elements */}
      <div className="absolute inset-0 opacity-20">
        <div className="absolute top-0 left-0 w-32 h-32 bg-white rounded-full -translate-x-16 -translate-y-16 animate-pulse"></div>
        <div className="absolute bottom-0 right-0 w-24 h-24 bg-white rounded-full translate-x-12 translate-y-12 animate-pulse" style={{ animationDelay: '1s' }}></div>
        <div className="absolute top-1/2 right-1/4 w-16 h-16 bg-white rounded-full opacity-50 animate-pulse" style={{ animationDelay: '2s' }}></div>
      </div>
      
      {/* Content */}
      <div className="relative z-10">
        <div className="flex items-start justify-between mb-6">
          <div className="flex-1">
            <div className="flex items-center mb-3">
              <span className="text-4xl mr-3 animate-bounce">{status.emoji}</span>
              <div>
                <h1 className="text-3xl font-bold mb-1 tracking-tight">{workspace.name}</h1>
                <div className="text-xl font-medium opacity-95">{status.title}</div>
              </div>
            </div>
            <p className="text-lg opacity-90 leading-relaxed max-w-2xl">
              {status.subtitle}
            </p>
          </div>
          
          {/* Business metrics showcase */}
          <div className="hidden md:flex flex-col items-end space-y-2 text-right">
            <div className="bg-white bg-opacity-20 backdrop-blur-sm rounded-lg p-3 min-w-[200px]">
              <div className="text-sm opacity-80">Business Value</div>
              <div className="text-2xl font-bold">€{businessValue.toLocaleString()}</div>
            </div>
            <div className="bg-white bg-opacity-20 backdrop-blur-sm rounded-lg p-3 min-w-[200px]">
              <div className="text-sm opacity-80">Assets Ready</div>
              <div className="text-2xl font-bold">{assetStats.completedAssets}/{assetStats.totalAssets}</div>
            </div>
            {finalDeliverables > 0 && (
              <div className="bg-white bg-opacity-20 backdrop-blur-sm rounded-lg p-3 min-w-[200px]">
                <div className="text-sm opacity-80">Final Deliverables</div>
                <div className="text-2xl font-bold">{finalDeliverables}</div>
              </div>
            )}
            
            {/* 🎯 Goal Achievement Metrics */}
            {!loadingGoals && goals.length > 0 && (
              <div className="bg-white bg-opacity-20 backdrop-blur-sm rounded-lg p-3 min-w-[200px]">
                <div className="text-sm opacity-80">Goal Achievement</div>
                <div className="text-2xl font-bold">
                  {goals.filter(g => g.completion_pct! >= 100).length}/{goals.length}
                </div>
                <div className="text-xs opacity-70">Goals Completed</div>
              </div>
            )}
            
            {goalValidation && (
              <div className="bg-white bg-opacity-20 backdrop-blur-sm rounded-lg p-3 min-w-[200px]">
                <div className="text-sm opacity-80">Validation Status</div>
                <div className="text-lg font-bold">
                  {goalValidation.validation_status === 'excellent' ? '🎯 Excellent' :
                   goalValidation.validation_status === 'good' ? '✅ Good' :
                   goalValidation.validation_status === 'needs_improvement' ? '⚠️ Improving' : '❌ Critical'}
                </div>
                <div className="text-xs opacity-70">
                  {goalValidation.overall_achievement.toFixed(0)}% Achievement
                </div>
              </div>
            )}
          </div>
        </div>

        {/* 🎯 Goal Progress Summary */}
        {!loadingGoals && goals.length > 0 && (
          <div className="mb-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {goals.slice(0, 3).map((goal) => (
                <div key={goal.id} className="bg-white bg-opacity-20 backdrop-blur-sm rounded-lg p-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium opacity-90">
                      {goal.metric_type.replace(/_/g, ' ').toUpperCase()}
                    </span>
                    <span className="text-xs opacity-80">
                      {goal.current_value}/{goal.target_value}
                    </span>
                  </div>
                  <div className="w-full bg-white bg-opacity-30 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all duration-500 ${
                        goal.completion_pct! >= 100 ? 'bg-green-300' :
                        goal.completion_pct! >= 70 ? 'bg-blue-300' :
                        goal.completion_pct! >= 30 ? 'bg-yellow-300' : 'bg-red-300'
                      }`}
                      style={{ width: `${Math.min(goal.completion_pct!, 100)}%` }}
                    />
                  </div>
                  <div className="text-xs opacity-80 mt-1">
                    {goal.completion_pct!.toFixed(0)}% Complete
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Progress visualization */}
        <div className="mb-6">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium opacity-90">Project Completion</span>
            <span className="text-sm font-bold">{Math.round(actualCompletionRate)}%</span>
          </div>
          <div className="w-full bg-white bg-opacity-30 rounded-full h-3 shadow-inner">
            <div
              className="bg-white h-3 rounded-full shadow-lg transition-all duration-1000 ease-out"
              style={{ width: `${actualCompletionRate}%` }}
            />
          </div>
          {finalizationStatus && (
            <div className="mt-2 text-xs opacity-80">
              {finalizationStatus.finalization_phase_active && (
                <span className="bg-green-400 text-green-900 px-2 py-1 rounded-full mr-2">🔧 Finalization Phase</span>
              )}
              {finalizationStatus.final_deliverables_completed > 0 && (
                <span className="bg-blue-400 text-blue-900 px-2 py-1 rounded-full">✅ {finalizationStatus.final_deliverables_completed} Final Deliverables</span>
              )}
            </div>
          )}
        </div>

        {/* Action buttons - Enhanced for immediate value perception */}
        <div className="flex gap-4 flex-wrap">
          {/* Primary CTA - Always visible, adapts based on project state */}
          <a
            href={`/projects/${workspace.id}/conversation`}
            className="group px-8 py-4 bg-white text-black rounded-xl font-bold text-lg hover:bg-gray-100 transform hover:scale-105 transition-all duration-200 shadow-2xl hover:shadow-3xl flex items-center min-w-[280px] justify-center"
          >
            <svg className="w-6 h-6 mr-3 group-hover:animate-bounce" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <div className="text-left">
              <div>{isProjectComplete ? 'Download & Use Now' : 'View Assets & Progress'}</div>
              <div className="text-sm font-normal opacity-75">€{businessValue.toLocaleString()} business value</div>
            </div>
          </a>
          
          {/* Secondary Actions */}
          <a
            href={`/projects/${workspace.id}/team`}
            className="group px-6 py-4 bg-black/30 backdrop-blur-sm border border-white/20 rounded-xl font-semibold text-base hover:bg-black/50 transform hover:scale-105 transition-all duration-200 flex items-center"
          >
            <svg className="w-5 h-5 mr-2 group-hover:animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            Talk to AI Team
          </a>
          
          {/* Conditional final deliverables highlight */}
          {isProjectComplete && finalDeliverables > 0 && (
            <a
              href={`/projects/${workspace.id}/conversation`}
              className="group px-6 py-4 bg-gradient-to-r from-green-400 to-emerald-500 text-white rounded-xl font-bold text-base hover:from-green-500 hover:to-emerald-600 transform hover:scale-105 transition-all duration-200 shadow-xl hover:shadow-2xl flex items-center animate-pulse"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div className="text-left">
                <div>Ready to Deploy!</div>
                <div className="text-sm font-normal opacity-90">{finalDeliverables} final deliverables</div>
              </div>
            </a>
          )}
        </div>
      </div>
    </div>
  )
}

export default ActionableHeroSection
