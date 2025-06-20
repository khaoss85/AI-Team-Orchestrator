"use client"

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const Sidebar = () => {
  const pathname = usePathname();
  
  const links = [
    { name: '🏠 Dashboard', href: '/', description: 'Overview e metriche' },
    { name: '💼 Progetti', href: '/projects', description: 'Workspace AI-driven' },
    { name: '👥 Team di Agenti', href: '/teams', description: 'Gestione agenti AI' },
    { name: '🛠️ Tool', href: '/tools', description: 'Strumenti disponibili' },
    { name: '📚 Knowledge Base', href: '/knowledge', description: 'Base di conoscenze' },
    { name: '💬 Feedback Umano', href: '/human-feedback', description: 'Revisioni e feedback' },
    { name: '⚙️ Impostazioni', href: '/settings', description: 'Configurazione sistema' },
  ];
  
  return (
    <aside className="bg-indigo-700 text-white w-64 hidden md:flex flex-col">
      <div className="p-6">
        <div className="text-xl font-bold mb-6">🤖 AI Orchestrator</div>
        <nav>
          <ul className="space-y-1">
            {links.map(({ name, href, description }) => (
              <li key={name}>
                <Link href={href} 
                      className={`block py-3 px-4 rounded-lg transition group ${
                        pathname === href ? 'bg-indigo-800 shadow-lg' : 'hover:bg-indigo-600'
                      }`}>
                  <div className="font-medium text-sm">{name}</div>
                  <div className="text-indigo-200 text-xs mt-0.5 opacity-75 group-hover:opacity-100">
                    {description}
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      </div>
      <div className="mt-auto p-6">
        <div className="bg-indigo-800 p-4 rounded-lg">
          <h3 className="font-medium text-sm flex items-center">
            🎯 Conversational AI
          </h3>
          <p className="text-indigo-200 text-xs mt-1">
            Nuova interfaccia conversazionale disponibile nei progetti
          </p>
          <button className="mt-3 text-xs bg-indigo-600 hover:bg-indigo-500 py-2 px-3 rounded-lg w-full transition-colors">
            📚 Guida Introduttiva
          </button>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;