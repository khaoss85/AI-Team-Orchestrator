'use client';

import React, { use } from 'react';
import Link from 'next/link';
import ProjectDeliverableDashboard from '@/components/ProjectDeliverableDashboard';

type Props = {
  params: Promise<{ id: string }>;
  searchParams?: { [key: string]: string | string[] | undefined };
};

export default function ProjectDeliverablesPage({ params: paramsPromise, searchParams }: Props) {
  const params = use(paramsPromise);
  const { id } = params;

  return (
    <div className="container mx-auto">
      {/* Breadcrumb */}
      <div className="mb-6">
        <Link href={`/projects/${id}`} className="text-indigo-600 hover:underline text-sm">
          ← Torna al progetto
        </Link>
        <h1 className="text-2xl font-semibold mt-2">Project Deliverables</h1>
        <p className="text-gray-600">Visualizza i risultati finali e output del progetto</p>
      </div>

      {/* Main Content */}
      <ProjectDeliverableDashboard workspaceId={id} />
    </div>
  );
}