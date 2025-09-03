'use client'

import React from 'react'
import { usePathname } from 'next/navigation'
import Sidebar from '@/components/Sidebar'
import MinimalFloatingSidebar from '@/components/MinimalFloatingSidebar'
import Header from '@/components/Header'

interface LayoutWrapperProps {
  children: React.ReactNode
}

export default function LayoutWrapper({ children }: LayoutWrapperProps) {
  const pathname = usePathname()
  const isConversationPage = pathname?.includes('/conversation')
  
  // Feature flag for minimal sidebar (default: false for safety)
  const useMinimalSidebar = process.env.NEXT_PUBLIC_ENABLE_MINIMAL_SIDEBAR === 'true'

  if (isConversationPage) {
    // Full-height layout for conversational UI (no sidebar for immersive experience)
    return (
      <div className="h-screen w-full">
        {children}
      </div>
    )
  }

  if (useMinimalSidebar) {
    // Minimal layout with floating sidebar only
    return (
      <div className="min-h-screen bg-gray-50 relative">
        <MinimalFloatingSidebar />
        <div className="pl-20"> {/* Offset content for floating sidebar */}
          <main className="p-4">
            {children}
          </main>
        </div>
      </div>
    )
  }

  // Standard layout with sidebar and header (legacy)
  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto p-4 bg-gray-50">
          {children}
        </main>
      </div>
    </div>
  )
}