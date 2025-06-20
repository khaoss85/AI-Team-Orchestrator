'use client'

import React from 'react'

export default function ConversationLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="h-screen w-full overflow-hidden bg-gray-50">
      {children}
    </div>
  )
}