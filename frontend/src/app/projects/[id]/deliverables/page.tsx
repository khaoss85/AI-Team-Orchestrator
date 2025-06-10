// frontend/src/app/projects/[id]/deliverables/page.tsx - DEPRECATED: REDIRECTS TO UNIFIED RESULTS

'use client';

import React, { use, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

type Props = {
  params: Promise<{ id: string }>;
  searchParams?: Promise<{ [key: string]: string | string[] | undefined }>;
};

export default function ProjectDeliverablesPage({ params: paramsPromise }: Props) {
  const params = use(paramsPromise);
  const { id } = params;
  const router = useRouter();

  // Auto-redirect to assets page after 3 seconds
  useEffect(() => {
    const timer = setTimeout(() => {
      router.push(`/projects/${id}/assets`);
    }, 3000);

    return () => clearTimeout(timer);
  }, [id, router]);

  const handleRedirectNow = () => {
    router.push(`/projects/${id}/assets`);
  };

  return (
    <div className="container mx-auto">
      {/* Migration Notice */}
      <div className="min-h-screen flex items-center justify-center">
        <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-8 text-center">
          <div className="mb-6">
            <div className="text-6xl mb-4">📋</div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Page Moved!</h1>
            <p className="text-gray-600">
              Deliverables are now part of our new <strong>Assets</strong> page for a better experience.
            </p>
          </div>

          <div className="mb-6 p-4 bg-purple-50 rounded-lg">
            <h3 className="font-semibold text-purple-800 mb-2">🚀 Enhanced Experience:</h3>
            <ul className="text-sm text-purple-700 text-left space-y-1">
              <li>• View deliverables and assets together</li>
              <li>• Rich content with proper markup</li>
              <li>• Business impact filtering</li>
              <li>• Export and sharing capabilities</li>
            </ul>
          </div>

          <div className="flex flex-col gap-3">
            <button
              onClick={handleRedirectNow}
              className="w-full bg-purple-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-purple-700 transition-colors"
            >
              Go to Assets Page Now
            </button>
            
            <Link
              href={`/projects/${id}`}
              className="text-gray-600 hover:text-gray-800 text-sm underline"
            >
              Back to Project Overview
            </Link>
          </div>

          <div className="mt-6 text-xs text-gray-500">
            <div className="flex items-center justify-center">
              <div className="w-3 h-3 bg-purple-600 rounded-full animate-pulse mr-2"></div>
              Redirecting automatically in 3 seconds...
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}