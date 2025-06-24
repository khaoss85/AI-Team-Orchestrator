// frontend/src/components/conversational/WorkspaceHealthArtifact.tsx
import React from 'react'
import { WorkspaceHealthMonitor } from '../WorkspaceHealthMonitor'

interface WorkspaceHealthArtifactProps {
  workspaceHealthStatus: any
  healthLoading: boolean
  onUnblock: (reason?: string) => Promise<{ success: boolean; message: string }>
  onRefresh: () => Promise<any>
  onResumeAutoGeneration?: () => Promise<{ success: boolean; message: string }>
}

export function WorkspaceHealthArtifact({
  workspaceHealthStatus,
  healthLoading,
  onUnblock,
  onRefresh,
  onResumeAutoGeneration
}: WorkspaceHealthArtifactProps) {
  return (
    <div className="bg-white rounded-lg">
      <WorkspaceHealthMonitor
        workspaceHealthStatus={workspaceHealthStatus}
        healthLoading={healthLoading}
        onUnblock={onUnblock}
        onRefresh={onRefresh}
        onResumeAutoGeneration={onResumeAutoGeneration}
      />
    </div>
  )
}