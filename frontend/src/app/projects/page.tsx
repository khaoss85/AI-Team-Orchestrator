'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { api } from '@/utils/api';
import { Workspace } from '@/types';

// Array di progetti suggeriti
const suggestedProjects = [
  {
    id: 'social-growth',
    name: 'Social Growth',
    description: 'Sviluppare strategie di crescita per account Instagram dedicato a bodybuilder',
    goal: 'Definire una strategia e un piano editoriale per l\'account Instagram dedicato a un pubblico maschile di bodybuilder con l\'obiettivo di crescere di 200 follower a settimana e aumentare l\'interazione dei post/Reales almeno del +10% settimana su settimana',
    budget: { max_amount: 1200, currency: 'EUR' },
    icon: '📱',
    color: 'from-purple-500 to-indigo-600',
  },
  {
    id: 'sport-performance',
    name: 'Sport Performance Boost',
    description: 'Programma di allenamento integrato (forza, cardio, mobilità, recupero) pensato per chi vuole elevare il proprio livello atletico in modo sostenibile',
    goal: 'Migliorare potenza, resistenza e capacità di recupero, ridurre il rischio infortuni, creare un regime di monitoraggio continuo dei progressi',
    budget: { max_amount: 800, currency: 'EUR' },
    icon: '💪',
    color: 'from-blue-500 to-blue-700',
  },
  {
    id: 'guitar-skills',
    name: 'Guitar Skill Upgrade',
    description: 'Percorso pratico che combina tecnica, teoria e pratica guidata (esercizi giornalieri, studio di brani, registrazioni e feedback)',
    goal: 'Aumentare fluidità e precisione, ampliare il repertorio personale, sviluppare un metodo di studio autonomo e regolare',
    budget: { max_amount: 600, currency: 'EUR' },
    icon: '🎸',
    color: 'from-yellow-500 to-orange-600',
  },
  {
    id: 'smart-investing',
    name: 'Smart Investing Guide',
    description: 'Sistema di analisi e raccomandazioni azionarie basato su fondamentali, trend di mercato e sentiment, con dashboard e alert personalizzati',
    goal: 'Costruire un portafoglio diversificato, supportare decisioni di acquisto/vendita consapevoli, mantenere un monitoraggio periodico dei rischi',
    budget: { max_amount: 1500, currency: 'EUR' },
    icon: '📊',
    color: 'from-green-500 to-emerald-600',
  },
  {
    id: 'mindful-habits',
    name: 'Mindful Habits Builder',
    description: 'Programma quotidiano di meditazione, respirazione profonda e journaling guidato',
    goal: 'Creare una routine di 10-15 min/die, ridurre lo stress auto-rilevato del 20% in 8 settimane, mantenere una streak di 30 giorni',
    budget: { max_amount: 400, currency: 'EUR' },
    icon: '🧘',
    color: 'from-teal-500 to-cyan-600',
  },
  {
    id: 'healthy-meal',
    name: 'Healthy Meal Prep',
    description: 'Sistema settimanale di pianificazione e batch-cooking di pasti equilibrati',
    goal: 'Preparare in casa l\'80% dei pasti, ridurre le spese food del 15% e rispettare i target macro-nutrizionali',
    budget: { max_amount: 700, currency: 'EUR' },
    icon: '🥗',
    color: 'from-lime-500 to-green-600',
  },
  {
    id: 'coding-upskill',
    name: 'Coding Upskill Sprint',
    description: 'Percorso intensivo su JavaScript/React con progetti hands-on e code-review',
    goal: 'Completare 3 mini-app full-stack in 12 settimane, ottenere una certificazione online e contribuire a un repo open-source',
    budget: { max_amount: 900, currency: 'EUR' },
    icon: '💻',
    color: 'from-blue-500 to-indigo-600',
  },
  {
    id: 'public-speaking',
    name: 'Public Speaking Boost',
    description: 'Laboratorio di speech-crafting, prove video e feedback peer-to-peer',
    goal: 'Tenere un talk pubblico entro 3 mesi, ottenere valutazioni ≥ 4/5 dal pubblico e ridurre le filler-words del 50%',
    budget: { max_amount: 550, currency: 'EUR' },
    icon: '🎤',
    color: 'from-red-500 to-pink-600',
  },
  {
    id: 'digital-minimalism',
    name: 'Digital Minimalism Reset',
    description: 'Sfida di 30 giorni per ridurre screen-time e riorganizzare device/notifiche',
    goal: 'Tagliare l\'uso smartphone del 25%, eliminare l\'80% delle app inutili e stabilire due blocchi giornalieri no-device',
    budget: { max_amount: 350, currency: 'EUR' },
    icon: '📱',
    color: 'from-gray-500 to-gray-700',
  },
  {
  id: 'outbound-mailup',
  name: 'B2B Outbound Sales Lists',
  description: 'Creazione e qualificazione di liste di prospect per campagne outbound di MailUp',
  goal: 'Raccogliere 500 contatti ICP (CMO/CTO di aziende SaaS europee) e suggerire almeno 3 sequenze email da impostare su Hubspot con target open-rate ≥ 30 % e Click-to-rate almeno del 10% in 6 settimane',
  budget: { max_amount: 1000, currency: 'EUR' },
  icon: '📧',
  color: 'from-rose-500 to-pink-600',
},
    {
  id: 'abm-target-accounts',
  name: 'ABM Target Accounts',
  description: 'Identificazione e ingaggio di 100 account enterprise ideali con outreach multicanale (email, LinkedIn, call)',
  goal: 'Fissare 20 discovery call e generare pipeline da 200 k € in 8 settimane',
  budget: { max_amount: 1200, currency: 'EUR' },
  icon: '🎯',
  color: 'from-indigo-500 to-violet-600',
},
{
  id: 'partner-prospecting',
  name: 'Channel Partner Prospecting',
  description: 'Costruzione di pipeline di partner (agency, reseller) per MailUp nel mercato DACH',
  goal: 'On-boardare 5 nuovi partner certificati con forecast 50 k € nel Q3',
  budget: { max_amount: 1500, currency: 'EUR' },
  icon: '🤝',
  color: 'from-emerald-500 to-teal-600',
},
{
  id: 'webinar-funnel',
  name: 'Webinar Demand Gen',
  description: 'Organizzazione di webinar educational e nurturing lead con sequenze email MailUp',
  goal: 'Ottenere 400 registrazioni e convertire 40 MQL in SQL entro 2 mesi',
  budget: { max_amount: 800, currency: 'EUR' },
  icon: '🎥',
  color: 'from-cyan-500 to-sky-600',
},
{
  id: 'customer-expansion',
  name: 'Customer Expansion Play',
  description: 'Segmentazione clienti attivi e campagne upsell/cross-sell automatizzate',
  goal: 'Aumentare l’ARPU del 15 % su 200 clienti entro fine trimestre',
  budget: { max_amount: 700, currency: 'EUR' },
  icon: '📈',
  color: 'from-green-500 to-lime-600',
},
];

// Componente per la card del progetto suggerito
function SuggestedProjectCard({ project, onClick }: { project: typeof suggestedProjects[number]; onClick: () => void }) {
  return (
    <div 
      onClick={onClick}
      className={`bg-gradient-to-br ${project.color} text-white rounded-lg shadow-md p-5 hover:shadow-lg transition transform hover:-translate-y-1 cursor-pointer`}
    >
      <div className="flex justify-between items-start mb-3">
        <h3 className="text-lg font-semibold">{project.name}</h3>
        <span className="text-2xl">{project.icon}</span>
      </div>
      <p className="text-sm text-white text-opacity-90 mb-3 line-clamp-2">
        {project.description}
      </p>
      <div className="text-xs text-white text-opacity-75">
        Budget: {project.budget.max_amount} {project.budget.currency}
      </div>
    </div>
  );
}

export default function ProjectsPage() {
  const router = useRouter();
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('existing'); // 'existing' o 'suggested'
  
  // Mock user ID for development
  const mockUserId = '123e4567-e89b-12d3-a456-426614174000';
  
  useEffect(() => {
    const fetchWorkspaces = async () => {
      try {
        setLoading(true);
        const data = await api.workspaces.list(mockUserId);
        setWorkspaces(data);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch workspaces:', err);
        setError('Impossibile caricare i progetti. Riprova più tardi.');
        // Per test, mostra dati fittizi
        setWorkspaces([
          {
            id: '1',
            name: 'Progetto Marketing Digitale',
            description: 'Campagna di marketing sui social media',
            user_id: mockUserId,
            status: 'active',
            goal: 'Aumentare la visibilità del brand',
            budget: { max_amount: 1000, currency: 'EUR' },
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
          {
            id: '2',
            name: 'Analisi Dati Utenti',
            description: 'Analisi comportamentale degli utenti sul sito web',
            user_id: mockUserId,
            status: 'created',
            goal: 'Identificare pattern di comportamento',
            budget: { max_amount: 500, currency: 'EUR' },
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        ]);
      } finally {
        setLoading(false);
      }
    };
    
    fetchWorkspaces();
  }, []);
  
  const handleProjectClick = (id: string) => {
    // Use the router to navigate programmatically
    router.push(`/projects/${id}`);
  };
  
  const handleSuggestedProjectClick = (project: typeof suggestedProjects[number]) => {
    // Salva i dati del template in localStorage per recuperarli nella pagina di creazione
    localStorage.setItem('projectTemplate', JSON.stringify({
      name: project.name,
      description: project.description,
      goal: project.goal,
      budget: project.budget
    }));
    
    // Naviga alla pagina di creazione nuovo progetto
    router.push('/projects/new');
  };
  
  return (
    <div className="container mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold">I Tuoi Progetti</h1>
        <Link href="/projects/new" className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition">
          Nuovo Progetto
        </Link>
      </div>
      
      {/* Tab Navigation */}
      <div className="flex border-b border-gray-200 mb-6">
        <button
          className={`px-4 py-2 font-medium text-sm ${activeTab === 'existing' ? 'text-indigo-600 border-b-2 border-indigo-500' : 'text-gray-500 hover:text-gray-700'}`}
          onClick={() => setActiveTab('existing')}
        >
          I Tuoi Progetti
        </button>
        <button
          className={`px-4 py-2 font-medium text-sm ${activeTab === 'suggested' ? 'text-indigo-600 border-b-2 border-indigo-500' : 'text-gray-500 hover:text-gray-700'}`}
          onClick={() => setActiveTab('suggested')}
        >
          Progetti Suggeriti
        </button>
      </div>
      
      {/* Tab Content */}
      {activeTab === 'existing' && (
        <>
          {loading ? (
            <div className="text-center py-10">
              <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-indigo-600 border-r-transparent"></div>
              <p className="mt-2 text-gray-600">Caricamento progetti...</p>
            </div>
          ) : error ? (
            <div className="bg-red-50 text-red-700 p-4 rounded-md mb-6">
              {error}
            </div>
          ) : workspaces.length === 0 ? (
            <div className="text-center py-10 bg-white rounded-lg shadow-sm">
              <h3 className="text-lg font-medium text-gray-600">Nessun progetto trovato</h3>
              <p className="text-gray-500 mt-2">Inizia creando il tuo primo progetto o scegli uno dei nostri modelli suggeriti</p>
              <div className="mt-4 flex gap-3 justify-center">
                <Link href="/projects/new" className="inline-block px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition">
                  Crea Progetto
                </Link>
                <button 
                  onClick={() => setActiveTab('suggested')} 
                  className="inline-block px-4 py-2 bg-green-600 text-white rounded-md text-sm hover:bg-green-700 transition"
                >
                  Progetti Suggeriti
                </button>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {workspaces.map((workspace) => (
                <div 
                  key={workspace.id}
                  onClick={() => handleProjectClick(workspace.id)}
                  className="bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition cursor-pointer"
                >
                  <div className="flex justify-between items-start mb-4">
                    <h2 className="text-lg font-medium text-gray-800">{workspace.name}</h2>
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      workspace.status === 'active' ? 'bg-green-100 text-green-800' :
                      workspace.status === 'created' ? 'bg-blue-100 text-blue-800' :
                      workspace.status === 'paused' ? 'bg-yellow-100 text-yellow-800' :
                      workspace.status === 'completed' ? 'bg-gray-100 text-gray-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {workspace.status === 'active' ? 'Attivo' :
                       workspace.status === 'created' ? 'Creato' :
                       workspace.status === 'paused' ? 'In pausa' :
                       workspace.status === 'completed' ? 'Completato' :
                       'Errore'}
                    </span>
                  </div>
                  
                  <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                    {workspace.description || 'Nessuna descrizione'}
                  </p>
                  
                  <div className="border-t pt-4 mt-4">
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <p className="text-gray-500">Obiettivo</p>
                        <p className="font-medium text-gray-800 truncate">
                          {workspace.goal || 'Non specificato'}
                        </p>
                      </div>
                      <div>
                        <p className="text-gray-500">Budget</p>
                        <p className="font-medium text-gray-800">
                          {workspace.budget && workspace.budget.max_amount && workspace.budget.currency
                            ? `${workspace.budget.max_amount} ${workspace.budget.currency}`
                            : 'Non specificato'}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
      
      {activeTab === 'suggested' && (
        <>
          <div className="mb-6">
            <p className="text-gray-600">
              Seleziona uno dei progetti suggeriti per iniziare rapidamente. Tutti i dettagli verranno precompilati automaticamente.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {suggestedProjects.map((project) => (
              <SuggestedProjectCard 
                key={project.id} 
                project={project} 
                onClick={() => handleSuggestedProjectClick(project)}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}