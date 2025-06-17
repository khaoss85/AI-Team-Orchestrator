'use client'

import React, { useState, useEffect } from 'react'

interface FeedbackNotificationBadgeProps {
  workspaceId: string
  onClick: () => void
  className?: string
}

const FeedbackNotificationBadge: React.FC<FeedbackNotificationBadgeProps> = ({
  workspaceId,
  onClick,
  className = ''
}) => {
  const [pendingCount, setPendingCount] = useState(0)
  const [urgentCount, setUrgentCount] = useState(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchPendingCount()
    
    // Poll for updates every 30 seconds
    const interval = setInterval(fetchPendingCount, 30000)
    return () => clearInterval(interval)
  }, [workspaceId])

  const fetchPendingCount = async () => {
    try {
      const response = await fetch(`http://localhost:8000/human-feedback/pending?workspace_id=${workspaceId}`)
      if (response.ok) {
        const data = await response.json()
        const requests = data.pending_requests || []
        setPendingCount(requests.length)
        
        // Count urgent requests (critical and high priority)
        const urgent = requests.filter((req: any) => 
          req.priority === 'critical' || req.priority === 'high'
        ).length
        setUrgentCount(urgent)
      }
    } catch (error) {
      console.error('Error fetching pending feedback count:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <button className={`relative ${className}`} disabled>
        <div className="w-5 h-5 bg-gray-300 rounded-full animate-pulse"></div>
      </button>
    )
  }

  if (pendingCount === 0) {
    return (
      <button 
        onClick={onClick}
        className={`relative text-gray-400 hover:text-gray-600 ${className}`}
        title="No pending reviews"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </button>
    )
  }

  return (
    <button 
      onClick={onClick}
      className={`relative ${className}`}
      title={`${pendingCount} deliverable${pendingCount !== 1 ? 's' : ''} ready for review${urgentCount > 0 ? ` (${urgentCount} urgent)` : ''}`}
    >
      {/* Main icon */}
      <svg 
        className={`w-6 h-6 ${urgentCount > 0 ? 'text-red-600' : 'text-blue-600'} hover:opacity-80`} 
        fill="none" 
        stroke="currentColor" 
        viewBox="0 0 24 24"
      >
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      
      {/* Notification badge */}
      <span className={`absolute -top-2 -right-2 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white rounded-full min-w-[1.25rem] h-5 ${
        urgentCount > 0 ? 'bg-red-600 animate-pulse' : 'bg-blue-600'
      }`}>
        {pendingCount > 99 ? '99+' : pendingCount}
      </span>
      
      {/* Urgent indicator */}
      {urgentCount > 0 && (
        <span className="absolute -top-1 -left-1 flex h-3 w-3">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
        </span>
      )}
    </button>
  )
}

export default FeedbackNotificationBadge