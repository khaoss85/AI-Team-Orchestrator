'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

interface Props {
  projectId: string;
  className?: string;
}

export const ProjectNavigationTabs: React.FC<Props> = ({ projectId, className = '' }) => {
  const pathname = usePathname();

  const tabs = [
    {
      id: 'overview',
      label: 'Overview',
      href: `/projects/${projectId}`,
      icon: '🏠',
      description: 'Project dashboard'
    },
    {
      id: 'results',
      label: 'Results',
      href: `/projects/${projectId}/results`,
      icon: '📊',
      description: 'All outputs & deliverables'
    },
    {
      id: 'assets',
      label: 'Assets',
      href: `/projects/${projectId}/assets`,
      icon: '📜',
      description: 'Version history & dependencies'
    },
    {
      id: 'ai-management',
      label: 'AI Management',
      href: `/projects/${projectId}/ai-management`,
      icon: '🤖',
      description: 'Real-time AI features'
    },
    {
      id: 'tasks',
      label: 'Tasks',
      href: `/projects/${projectId}/tasks`,
      icon: '✅',
      description: 'Task logs & performance'
    },
    {
      id: 'team',
      label: 'Team',
      href: `/projects/${projectId}/team`,
      icon: '👥',
      description: 'Agents & collaboration'
    },
    {
      id: 'settings',
      label: 'Settings',
      href: `/projects/${projectId}/settings`,
      icon: '⚙️',
      description: 'Project configuration'
    }
  ];

  const isActiveTab = (href: string) => {
    if (href === `/projects/${projectId}`) {
      return pathname === href;
    }
    return pathname.startsWith(href);
  };

  return (
    <div className={`bg-white border-b border-gray-200 ${className}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex space-x-8 overflow-x-auto">
          {tabs.map((tab) => (
            <Link
              key={tab.id}
              href={tab.href}
              className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors whitespace-nowrap ${
                isActiveTab(tab.href)
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="text-lg">{tab.icon}</span>
              <span>{tab.label}</span>
              <span className="text-xs text-gray-400 hidden lg:block">
                {tab.description}
              </span>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
};