'use client'

import React from 'react';
import { useSearchParams } from 'next/navigation';
import UserFriendlyFeedbackDashboard from '@/components/UserFriendlyFeedbackDashboard';

export default function HumanFeedbackPage() {
  const searchParams = useSearchParams();
  const workspaceId = searchParams.get('workspace_id');

  return (
    <div className="container mx-auto">
      <UserFriendlyFeedbackDashboard workspaceId={workspaceId || undefined} />
    </div>
  );
}