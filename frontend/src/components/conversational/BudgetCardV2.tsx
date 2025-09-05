'use client'

import React from 'react'
import BudgetUsageChatV2 from './BudgetUsageChatV2'

interface BudgetCardV2Props {
  workspaceId: string
}

/**
 * Enhanced Budget Card that automatically switches between:
 * - Real OpenAI Usage API data when available
 * - Legacy quota tracking as fallback
 * 
 * This replaces the original BudgetCard component
 */
export default function BudgetCardV2({ workspaceId }: BudgetCardV2Props) {
  return <BudgetUsageChatV2 workspaceId={workspaceId} />
}