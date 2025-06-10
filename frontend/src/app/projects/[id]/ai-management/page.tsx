'use client';

import React, { use } from 'react';
import { AssetManagementShowcase } from '@/components/assets/AssetManagementShowcase';

interface Props {
  params: Promise<{ id: string }>;
}

export default function AIManagementPage({ params: paramsPromise }: Props) {
  const params = use(paramsPromise);
  const workspaceId = params.id;

  return (
    <AssetManagementShowcase workspaceId={workspaceId} />
  );
}