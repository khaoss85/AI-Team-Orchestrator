'use client';

import React, { useState, useEffect, use } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { api } from '@/utils/api';
import type { Workspace } from '@/types';
import ConfirmModal from '@/components/ConfirmModal';

interface Props {
  params: Promise<{ id: string }>
}

export default function ProjectSettingsPage({ params: paramsPromise }: Props) {
  const params = use(paramsPromise);
  const id = params.id;
  const router = useRouter();

  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  // Form states
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [goal, setGoal] = useState('');
  const [maxBudget, setMaxBudget] = useState<number>(10);
  const [maxIterations, setMaxIterations] = useState<number>(3);
  
  // Advanced settings
  const [qualityThreshold, setQualityThreshold] = useState<number>(85);
  const [maxConcurrentTasks, setMaxConcurrentTasks] = useState<number>(3);
  const [taskTimeout, setTaskTimeout] = useState<number>(150);
  const [enableQualityAssurance, setEnableQualityAssurance] = useState<boolean>(true);
  const [deliverableThreshold, setDeliverableThreshold] = useState<number>(50);
  const [maxDeliverablesPerProject, setMaxDeliverablesPerProject] = useState<number>(3);

  // Delete confirmation
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);
  
  // Settings test state
  const [testingSettings, setTestingSettings] = useState(false);
  const [settingsTestResult, setSettingsTestResult] = useState<any>(null);

  useEffect(() => {
    fetchWorkspace();
  }, [id]);

  const fetchWorkspace = async () => {
    try {
      setLoading(true);
      const data = await api.workspaces.get(id);
      setWorkspace(data);
      
      // Initialize form with current values
      setName(data.name || '');
      setDescription(data.description || '');
      setGoal(data.goal || '');
      setMaxBudget(data.budget?.max_budget || 10);
      setMaxIterations(data.budget?.max_iterations || 3);
      
      // Load advanced settings
      const settings = data.budget?.settings || {};
      setQualityThreshold(settings.quality_threshold || 85);
      setMaxConcurrentTasks(settings.max_concurrent_tasks || 3);
      setTaskTimeout(settings.task_timeout || 150);
      setEnableQualityAssurance(settings.enable_quality_assurance !== false);
      setDeliverableThreshold(settings.deliverable_threshold || 50);
      setMaxDeliverablesPerProject(settings.max_deliverables || 3);
      
      setError(null);
    } catch (e: any) {
      setError(e.message || 'Unable to load project');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!workspace) return;

    try {
      setSaving(true);
      setError(null);

      await api.workspaces.update(id, {
        name,
        description,
        goal,
        budget: {
          max_budget: maxBudget,
          max_iterations: maxIterations,
          settings: {
            quality_threshold: qualityThreshold,
            max_concurrent_tasks: maxConcurrentTasks,
            task_timeout: taskTimeout,
            enable_quality_assurance: enableQualityAssurance,
            deliverable_threshold: deliverableThreshold,
            max_deliverables: maxDeliverablesPerProject
          }
        }
      });

      // Show success notification
      alert('Project settings updated successfully!');
      
      // Refresh workspace data
      await fetchWorkspace();
    } catch (e: any) {
      setError(e.message || 'Failed to update project');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    try {
      setDeleting(true);
      await api.workspaces.delete(id);
      router.push('/projects');
    } catch (e: any) {
      setError(e.message || 'Failed to delete project');
      setDeleting(false);
    }
  };

  const testSettings = async () => {
    try {
      setTestingSettings(true);
      setSettingsTestResult(null);
      
      const result = await api.workspaces.getSettings(id);
      setSettingsTestResult(result);
      
      // Show success notification with settings values
      const settingsInfo = Object.entries(result.settings)
        .map(([key, value]) => `${key}: ${value}`)
        .join(', ');
      alert(`Settings verified successfully!\n\n${settingsInfo}`);
    } catch (e: any) {
      setSettingsTestResult({ error: e.message });
      alert(`Failed to test settings: ${e.message}`);
    } finally {
      setTestingSettings(false);
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto py-20 text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">Loading project settings...</p>
      </div>
    );
  }

  if (error && !workspace) {
    return (
      <div className="container mx-auto py-20 text-center text-red-600">
        {error}
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-4xl space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Link href={`/projects/${id}`} className="text-indigo-600 hover:underline text-sm">
            ← Back to Project
          </Link>
          <h1 className="text-3xl font-bold text-gray-900 mt-2">Project Settings</h1>
        </div>
      </div>

      {/* Settings Form */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6 space-y-6">
          {/* Basic Information */}
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Basic Information</h2>
            
            <div className="space-y-4">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                  Project Name
                </label>
                <input
                  type="text"
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  placeholder="Enter project name"
                />
              </div>

              <div>
                <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  placeholder="Describe your project"
                />
              </div>

              <div>
                <label htmlFor="goal" className="block text-sm font-medium text-gray-700 mb-1">
                  Project Goal
                </label>
                <textarea
                  id="goal"
                  value={goal}
                  onChange={(e) => setGoal(e.target.value)}
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  placeholder="What is the main goal of this project?"
                />
              </div>
            </div>
          </div>

          {/* Budget & Basic Limits */}
          <div className="border-t pt-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Budget & Basic Limits</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="budget" className="block text-sm font-medium text-gray-700 mb-1">
                  Maximum Budget ($)
                </label>
                <input
                  type="number"
                  id="budget"
                  value={maxBudget}
                  onChange={(e) => setMaxBudget(Number(e.target.value))}
                  min={0}
                  step={0.5}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
                <p className="text-xs text-gray-500 mt-1">AI usage cost limit for this project</p>
              </div>

              <div>
                <div className="flex items-center">
                  <label htmlFor="iterations" className="block text-sm font-medium text-gray-700 mb-1">
                    Max Iterations per Task
                  </label>
                  <div className="relative ml-1 group">
                    <svg className="w-4 h-4 text-gray-400 hover:text-gray-600 cursor-help" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-1 bg-gray-800 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-10">
                      Number of improvement cycles each task can go through before being marked complete
                    </div>
                  </div>
                </div>
                <input
                  type="number"
                  id="iterations"
                  value={maxIterations}
                  onChange={(e) => setMaxIterations(Number(e.target.value))}
                  min={1}
                  max={10}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
                <p className="text-xs text-gray-500 mt-1">Maximum improvement loops per task</p>
              </div>
            </div>
            
            {/* Budget Monitoring Notice */}
            <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-start space-x-2">
                <span className="text-blue-600 text-sm">💰</span>
                <div className="flex-1">
                  <p className="text-sm text-blue-800">
                    <strong>Monitor your budget usage:</strong> For real-time budget tracking and OpenAI quota monitoring, 
                    check the <Link href={`/projects/${id}/conversation`} className="font-semibold text-blue-700 underline hover:text-blue-900">Budget & Usage</Link> chat 
                    in the conversation panel.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Advanced Settings */}
          <div className="border-t pt-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Advanced Settings</h2>
            
            <div className="space-y-6">
              {/* Quality Settings */}
              <div>
                <h3 className="text-lg font-medium text-gray-800 mb-3">Quality Assurance</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <div className="flex items-center mb-1">
                      <label htmlFor="qualityThreshold" className="text-sm font-medium text-gray-700">
                        Quality Threshold (%)
                      </label>
                      <div className="relative ml-1 group">
                        <svg className="w-4 h-4 text-gray-400 hover:text-gray-600 cursor-help" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-1 bg-gray-800 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-10">
                          Minimum quality score required for content to be approved (0-100)
                        </div>
                      </div>
                    </div>
                    <input
                      type="number"
                      id="qualityThreshold"
                      value={qualityThreshold}
                      onChange={(e) => setQualityThreshold(Number(e.target.value))}
                      min={0}
                      max={100}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  </div>

                  <div>
                    <div className="flex items-center mb-1">
                      <label htmlFor="enableQA" className="text-sm font-medium text-gray-700">
                        Enable Quality Assurance
                      </label>
                      <div className="relative ml-1 group">
                        <svg className="w-4 h-4 text-gray-400 hover:text-gray-600 cursor-help" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-1 bg-gray-800 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-10">
                          Enable AI-driven quality evaluation and enhancement
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="enableQA"
                        checked={enableQualityAssurance}
                        onChange={(e) => setEnableQualityAssurance(e.target.checked)}
                        className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                      />
                      <span className="ml-2 text-sm text-gray-600">
                        {enableQualityAssurance ? 'Enabled' : 'Disabled'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Execution Settings */}
              <div>
                <h3 className="text-lg font-medium text-gray-800 mb-3">Task Execution</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <div className="flex items-center mb-1">
                      <label htmlFor="concurrentTasks" className="text-sm font-medium text-gray-700">
                        Max Concurrent Tasks
                      </label>
                      <div className="relative ml-1 group">
                        <svg className="w-4 h-4 text-gray-400 hover:text-gray-600 cursor-help" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-1 bg-gray-800 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-10">
                          Maximum number of tasks that can run simultaneously (1-10)
                        </div>
                      </div>
                    </div>
                    <input
                      type="number"
                      id="concurrentTasks"
                      value={maxConcurrentTasks}
                      onChange={(e) => setMaxConcurrentTasks(Number(e.target.value))}
                      min={1}
                      max={10}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  </div>

                  <div>
                    <div className="flex items-center mb-1">
                      <label htmlFor="taskTimeout" className="text-sm font-medium text-gray-700">
                        Task Timeout (seconds)
                      </label>
                      <div className="relative ml-1 group">
                        <svg className="w-4 h-4 text-gray-400 hover:text-gray-600 cursor-help" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-1 bg-gray-800 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-10">
                          Maximum time a single task can run before being terminated (30-600 seconds)
                        </div>
                      </div>
                    </div>
                    <input
                      type="number"
                      id="taskTimeout"
                      value={taskTimeout}
                      onChange={(e) => setTaskTimeout(Number(e.target.value))}
                      min={30}
                      max={600}
                      step={10}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  </div>
                </div>
              </div>

              {/* Deliverable Settings */}
              <div>
                <h3 className="text-lg font-medium text-gray-800 mb-3">Deliverables</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <div className="flex items-center mb-1">
                      <label htmlFor="deliverableThreshold" className="text-sm font-medium text-gray-700">
                        Completion Threshold (%)
                      </label>
                      <div className="relative ml-1 group">
                        <svg className="w-4 h-4 text-gray-400 hover:text-gray-600 cursor-help" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-1 bg-gray-800 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-10">
                          Minimum task completion percentage before deliverables can be created (0-100)
                        </div>
                      </div>
                    </div>
                    <input
                      type="number"
                      id="deliverableThreshold"
                      value={deliverableThreshold}
                      onChange={(e) => setDeliverableThreshold(Number(e.target.value))}
                      min={0}
                      max={100}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  </div>

                  <div>
                    <div className="flex items-center mb-1">
                      <label htmlFor="maxDeliverables" className="text-sm font-medium text-gray-700">
                        Max Deliverables
                      </label>
                      <div className="relative ml-1 group">
                        <svg className="w-4 h-4 text-gray-400 hover:text-gray-600 cursor-help" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-1 bg-gray-800 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-10">
                          Maximum number of deliverables that can be created for this project (1-10)
                        </div>
                      </div>
                    </div>
                    <input
                      type="number"
                      id="maxDeliverables"
                      value={maxDeliverablesPerProject}
                      onChange={(e) => setMaxDeliverablesPerProject(Number(e.target.value))}
                      min={1}
                      max={10}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Project Status */}
          <div className="border-t pt-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Project Status</h2>
            
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <p className="text-gray-600">Status</p>
                  <p className="font-semibold capitalize">{workspace?.status || 'active'}</p>
                </div>
                <div>
                  <p className="text-gray-600">Created</p>
                  <p className="font-semibold">
                    {workspace?.created_at ? new Date(workspace.created_at).toLocaleDateString() : 'Unknown'}
                  </p>
                </div>
                <div>
                  <p className="text-gray-600">Budget Used</p>
                  <p className="font-semibold">
                    ${workspace?.total_cost?.toFixed(2) || '0.00'} / ${maxBudget.toFixed(2)}
                  </p>
                </div>
                <div>
                  <p className="text-gray-600">ID</p>
                  <p className="font-mono text-xs">{id.substring(0, 8)}...</p>
                </div>
              </div>
            </div>
          </div>

          {/* Save Button */}
          <div className="flex justify-between items-center pt-4">
            <button
              onClick={testSettings}
              disabled={testingSettings}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {testingSettings ? 'Testing...' : 'Test Settings'}
            </button>
            
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-600 text-sm">
              {error}
            </div>
          )}

          {/* Settings Test Result */}
          {settingsTestResult && (
            <div className={`border rounded-lg p-4 text-sm ${
              settingsTestResult.error 
                ? 'bg-red-50 border-red-200 text-red-600' 
                : 'bg-green-50 border-green-200 text-green-600'
            }`}>
              <h4 className="font-semibold mb-2">Settings Test Result:</h4>
              {settingsTestResult.error ? (
                <p>Error: {settingsTestResult.error}</p>
              ) : (
                <pre className="whitespace-pre-wrap">
                  {JSON.stringify(settingsTestResult, null, 2)}
                </pre>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Danger Zone */}
      <div className="bg-white rounded-lg shadow-sm border border-red-200">
        <div className="p-6">
          <h2 className="text-xl font-semibold text-red-600 mb-4">Danger Zone</h2>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-red-50 rounded-lg">
              <div>
                <h3 className="font-semibold text-gray-900">Delete Project</h3>
                <p className="text-sm text-gray-600 mt-1">
                  Permanently delete this project and all associated data. This action cannot be undone.
                </p>
              </div>
              <button
                onClick={() => setShowDeleteConfirm(true)}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Delete Project
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      <ConfirmModal
        isOpen={showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(false)}
        onConfirm={handleDelete}
        title="Delete Project"
        message={`Are you sure you want to delete "${workspace?.name}"? This will permanently delete all tasks, agents, and deliverables associated with this project.`}
        confirmText="Delete Project"
        confirmButtonClass="bg-red-600 hover:bg-red-700"
        loading={deleting}
      />
    </div>
  );
}