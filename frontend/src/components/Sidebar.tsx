"use client"

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const Sidebar = () => {
  const pathname = usePathname();
  
  const links = [
    { name: 'Dashboard', href: '/' },
    { name: 'Progetti', href: '/projects' },
    { name: 'Team di Agenti', href: '/teams' },
    { name: 'Knowledge Base', href: '/knowledge' },
    { name: 'Impostazioni', href: '/settings' },
  ];
  
  return (
    <aside className="bg-indigo-700 text-white w-64 hidden md:flex flex-col">
      <div className="p-6">
        <div className="text-xl font-bold mb-6">AI Orchestrator</div>
        <nav>
          <ul className="space-y-2">
            {links.map(({ name, href }) => (
              <li key={name}>
                <Link href={href} 
                      className={`block py-2.5 px-4 rounded transition ${
                        pathname === href ? 'bg-indigo-800' : 'hover:bg-indigo-600'
                      }`}>
                  {name}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      </div>
      <div className="mt-auto p-6">
        <div className="bg-indigo-800 p-4 rounded-lg">
          <h3 className="font-medium text-sm">Aiuto</h3>
          <p className="text-indigo-200 text-xs mt-1">
            Hai bisogno di assistenza con la piattaforma?
          </p>
          <button className="mt-2 text-xs bg-indigo-600 py-1.5 px-3 rounded w-full">
            Documentazione
          </button>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;