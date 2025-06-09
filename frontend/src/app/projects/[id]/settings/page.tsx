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

  // Delete confirmation
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);

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
          max_iterations: maxIterations
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

          {/* Budget & Limits */}
          <div className="border-t pt-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Budget & Limits</h2>
            
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
                <label htmlFor="iterations" className="block text-sm font-medium text-gray-700 mb-1">
                  Max Iterations per Task
                </label>
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
          <div className="flex justify-end pt-4">
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