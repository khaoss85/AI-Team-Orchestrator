'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Home, FileText, User } from 'lucide-react'

interface MinimalSidebarItem {
  icon: React.ComponentType<{ className?: string }>
  label: string
  href: string
  ariaLabel: string
}

const MinimalFloatingSidebar: React.FC = () => {
  const [isExpanded, setIsExpanded] = useState(false)
  const pathname = usePathname()
  
  const items: MinimalSidebarItem[] = [
    { 
      icon: Home, 
      label: 'Home', 
      href: '/', 
      ariaLabel: 'Navigate to home dashboard'
    },
    { 
      icon: FileText, 
      label: 'Library', 
      href: '/library', 
      ariaLabel: 'Open document library and knowledge base'
    },
    { 
      icon: User, 
      label: 'Profile', 
      href: '/profile', 
      ariaLabel: 'View profile and user settings'
    }
  ]

  const isActive = (href: string) => {
    if (href === '/') {
      return pathname === '/' || pathname === '/projects'
    }
    return pathname.startsWith(href)
  }

  return (
    <aside 
      className={`
        fixed left-4 top-1/2 -translate-y-1/2 z-50
        bg-white border border-gray-200 rounded-xl shadow-sm
        transition-all duration-200 ease-in-out
        ${isExpanded ? 'w-48' : 'w-12'}
      `}
      onMouseEnter={() => setIsExpanded(true)}
      onMouseLeave={() => setIsExpanded(false)}
    >
      <nav className="p-2 space-y-1">
        {items.map(({ icon: Icon, label, href, ariaLabel }) => {
          const active = isActive(href)
          
          return (
            <Link
              key={href}
              href={href}
              className={`
                flex items-center p-3 rounded-lg transition-all duration-200
                ${active 
                  ? 'bg-gray-100 text-gray-900' 
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                }
                ${isExpanded ? 'justify-start' : 'justify-center'}
              `}
              aria-label={ariaLabel}
              title={!isExpanded ? label : undefined}
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              {isExpanded && (
                <span className="ml-3 text-sm font-medium whitespace-nowrap">
                  {label}
                </span>
              )}
            </Link>
          )
        })}
      </nav>
    </aside>
  )
}

export default MinimalFloatingSidebar