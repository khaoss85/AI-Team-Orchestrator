'use client'

import * as React from 'react'

interface ScrollAreaProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string
  children?: React.ReactNode
}

export function ScrollArea({ 
  children, 
  className = '', 
  ...props 
}: ScrollAreaProps) {
  return (
    <div 
      className={`relative overflow-auto ${className}`} 
      {...props}
    >
      {children}
    </div>
  )
}

export function ScrollBar({ 
  orientation = 'vertical',
  className = '' 
}: { 
  orientation?: 'vertical' | 'horizontal'
  className?: string 
}) {
  return (
    <div 
      className={`
        absolute bg-gray-300 rounded-full transition-all
        ${orientation === 'vertical' 
          ? 'right-1 top-0 bottom-0 w-2 hover:w-3' 
          : 'bottom-1 left-0 right-0 h-2 hover:h-3'}
        ${className}
      `}
    />
  )
}