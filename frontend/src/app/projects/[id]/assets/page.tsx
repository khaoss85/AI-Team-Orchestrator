// frontend/src/app/projects/[id]/assets/page.tsx - DEPRECATED: REDIRECTS TO UNIFIED RESULTS

'use client';

import React, { use, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

type Props = {
  params: Promise<{ id: string }>;
  searchParams?: Promise<{ [key: string]: string | string[] | undefined }>;
};

export default function ProjectAssetsPage({ params: paramsPromise }: Props) {
  const params = use(paramsPromise);
  const { id } = params;
  const router = useRouter();

  // Auto-redirect to unified results after 3 seconds
  useEffect(() => {
    const timer = setTimeout(() => {
      router.push(`/projects/${id}/results?filter=readyToUse`);
    }, 3000);

    return () => clearTimeout(timer);
  }, [id, router]);

  const handleRedirectNow = () => {
    router.push(`/projects/${id}/results?filter=readyToUse`);
  };

  return (
    <div className="container mx-auto">
      {/* Migration Notice */}
      <div className="min-h-screen flex items-center justify-center">
        <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-8 text-center">
          <div className="mb-6">
            <div className="text-6xl mb-4">📊</div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Page Moved!</h1>
            <p className="text-gray-600">
              Assets are now part of our new <strong>Unified Results</strong> view for a better experience.
            </p>
          </div>

          <div className="mb-6 p-4 bg-blue-50 rounded-lg">
            <h3 className="font-semibold text-blue-800 mb-2">✨ New Features:</h3>
            <ul className="text-sm text-blue-700 text-left space-y-1">
              <li>• View assets and deliverables together</li>
              <li>• Smart filters (Ready to Use, High Impact)</li>
              <li>• Enhanced content with rich markup</li>
              <li>• Export and bulk actions</li>
            </ul>
          </div>

          <div className="flex flex-col gap-3">
            <button
              onClick={handleRedirectNow}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 transition-colors"
            >
              Go to Unified Results Now
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
              <div className="w-3 h-3 bg-blue-600 rounded-full animate-pulse mr-2"></div>
              Redirecting automatically in 3 seconds...
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}