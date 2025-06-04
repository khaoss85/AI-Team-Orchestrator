// frontend/src/app/projects/[id]/assets/page.tsx - DEDICATED ASSET PAGE

'use client';

import React, { use } from 'react';
import Link from 'next/link';
import AssetDashboard from '@/components/AssetDashboard';

type Props = {
  params: Promise<{ id: string }>;
  searchParams?: Promise<{ [key: string]: string | string[] | undefined }>;
};

export default function ProjectAssetsPage({ params: paramsPromise }: Props) {
  const params = use(paramsPromise);
  const { id } = params;

  return (
    <div className="container mx-auto">
      {/* Breadcrumb */}
      <div className="mb-6">
        <Link href={`/projects/${id}`} className="text-indigo-600 hover:underline text-sm">
          ← Torna al progetto
        </Link>
        <h1 className="text-2xl font-semibold mt-2">Asset Azionabili</h1>
        <p className="text-gray-600">Visualizza e gestisci tutti gli asset prodotti dal progetto</p>
      </div>

      {/* Main Asset Dashboard */}
      <AssetDashboard workspaceId={id} />
    </div>
  );
}