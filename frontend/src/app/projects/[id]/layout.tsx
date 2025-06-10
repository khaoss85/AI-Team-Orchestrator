'use client';

import React, { use } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ProjectNavigationTabs } from '@/components/ProjectNavigationTabs';

interface Props {
  children: React.ReactNode;
  params: Promise<{ id: string }>;
}

export default function ProjectLayout({ children, params: paramsPromise }: Props) {
  const params = use(paramsPromise);
  const projectId = params.id;
  const pathname = usePathname();
  
  // Nascondi il menu per la pagina di configurazione
  const isConfigurePage = pathname.includes('/configure');

  return (
    <div>
      {!isConfigurePage && (
        <>
          {/* Project Navigation with Breadcrumb */}
          <div className="bg-white border-b border-gray-200">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              {/* Breadcrumb */}
              <div className="flex items-center space-x-2 text-sm py-3 border-b border-gray-100">
                <Link href="/projects" className="text-blue-600 hover:text-blue-800">
                  Projects
                </Link>
                <span className="text-gray-400">/</span>
                <span className="text-gray-900 font-medium">Project {projectId.slice(0, 8)}...</span>
              </div>
            </div>
          </div>
          
          <ProjectNavigationTabs projectId={projectId} />
        </>
      )}

      {/* Page Content */}
      <div>
        {children}
      </div>
    </div>
  );
}