'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { api } from '@/utils/api';
import { Workspace } from '@/types';
import QuotaNotification from '@/components/QuotaNotification';
import { useQuotaMonitor } from '@/hooks/useQuotaMonitor';

// Array of suggested projects
const suggestedProjects = [
  {
    id: 'social-growth',
    name: 'Social Growth',
    description: 'Develop growth strategies for Instagram account dedicated to bodybuilders',
    goal: 'DELIVERABLES: (1) Complete Instagram content calendar with 30 posts/reels optimized for bodybuilder audience, (2) Growth strategy document with specific hashtag lists, posting times, and engagement tactics, (3) Templates for 5 high-performing post types (transformation posts, workout demos, nutrition tips, motivation quotes, behind-scenes), (4) Competitor analysis report identifying key accounts and their successful content patterns, (5) Weekly tracking dashboard template to monitor growth and engagement',
    budget: { max_amount: 1200, currency: 'EUR' },
    icon: '📱',
    color: 'from-purple-500 to-indigo-600',
  },
  {
    id: 'sport-performance',
    name: 'Sport Performance Boost',
    description: 'Integrated training program (strength, cardio, mobility, recovery) designed for those who want to sustainably elevate their athletic level',
    goal: 'DELIVERABLES: (1) Personalized 12-week training program with strength, cardio, mobility, and recovery phases including daily workout plans and progressive overload schedules, (2) Nutrition plan with macro calculations, meal timing, and supplement recommendations based on training goals, (3) Injury prevention assessment with mobility tests, corrective exercises, and movement pattern analysis, (4) Performance tracking spreadsheet with strength metrics, cardio benchmarks, and recovery indicators, (5) Video exercise library with proper form demonstrations and common mistakes, (6) Weekly check-in protocols and program adjustment guidelines for continuous improvement',
    budget: { max_amount: 800, currency: 'EUR' },
    icon: '💪',
    color: 'from-blue-500 to-blue-700',
  },
  {
    id: 'guitar-skills',
    name: 'Guitar Skill Upgrade',
    description: 'Practical path combining technique, theory and guided practice (daily exercises, song study, recordings and feedback)',
    goal: 'DELIVERABLES: (1) Personalized practice schedule with daily 30-minute sessions targeting technique, theory, and repertoire building, (2) Song collection across different genres with difficulty progression and practice recordings, (3) Technical exercises program covering scales, arpeggios, chord progressions, and fingerpicking patterns, (4) Music theory guide with chord progressions, scale relationships, and improvisation frameworks, (5) Recording studio setup guide and monthly performance recordings to track progress, (6) Practice journal template and goal-setting framework for continued learning',
    budget: { max_amount: 600, currency: 'EUR' },
    icon: '🎸',
    color: 'from-yellow-500 to-orange-600',
  },
  {
    id: 'smart-investing',
    name: 'Smart Investing Guide',
    description: 'Stock analysis and recommendation system based on fundamentals, market trends and sentiment, with personalized dashboard and alerts',
    goal: 'DELIVERABLES: (1) Personalized investment portfolio allocation with specific stock picks and % allocation for different investment levels, (2) Excel/Google Sheets portfolio tracker with automated P&L calculation and rebalancing alerts, (3) Monthly stock screening reports with buy/sell recommendations based on fundamental analysis, (4) Risk assessment questionnaire and personalized risk profile report, (5) 12-month investment calendar with optimal timing for different asset classes, (6) Emergency exit strategy playbook for market downturns',
    budget: { max_amount: 1500, currency: 'EUR' },
    icon: '📊',
    color: 'from-green-500 to-emerald-600',
  },
  {
    id: 'mindful-habits',
    name: 'Mindful Habits Builder',
    description: 'Daily program of meditation, deep breathing and guided journaling',
    goal: 'DELIVERABLES: (1) Personalized mindfulness routine with guided meditation scripts, breathing exercises, and journaling prompts tailored to individual needs, (2) Daily practice tracker with habit-building milestones, streak rewards, and progress visualization, (3) Stress assessment tools with weekly check-ins and improvement measurements, (4) Mindfulness resource library including audio guides, reading materials, and mobile apps recommendations, (5) Emergency stress-relief toolkit with quick techniques for high-pressure situations, (6) Long-term wellness plan with advanced practices and community integration',
    budget: { max_amount: 400, currency: 'EUR' },
    icon: '🧘',
    color: 'from-teal-500 to-cyan-600',
  },
  {
    id: 'healthy-meal',
    name: 'Healthy Meal Prep',
    description: 'Weekly planning and batch-cooking system for balanced meals',
    goal: 'DELIVERABLES: (1) Weekly meal planning system with 28 balanced recipes covering breakfast, lunch, dinner, and snacks with macro calculations, (2) Batch-cooking guide with prep schedules, storage methods, and reheating instructions for maximum freshness, (3) Smart shopping lists organized by store sections with seasonal ingredient substitutions and cost-optimization tips, (4) Kitchen equipment recommendations and meal prep container system for efficient storage, (5) Macro tracking spreadsheet with daily targets and weekly nutrition analysis, (6) Emergency meal solutions and healthy takeout alternatives for busy days',
    budget: { max_amount: 700, currency: 'EUR' },
    icon: '🥗',
    color: 'from-lime-500 to-green-600',
  },
  {
    id: 'coding-upskill',
    name: 'Coding Upskill Sprint',
    description: 'Intensive JavaScript/React path with hands-on projects and code reviews',
    goal: 'DELIVERABLES: (1) Three complete full-stack applications: E-commerce store (React+Node.js+MongoDB), Social media dashboard (Next.js+PostgreSQL), Task management app (React+Express+Firebase), (2) GitHub repository with clean code, documentation, and deployment instructions for each app, (3) Technical portfolio website showcasing all projects with live demos, (4) Code review checklist and best practices guide document, (5) Open-source contribution strategy and target repos identification, (6) Mock interview preparation with coding challenge solutions and practice schedule',
    budget: { max_amount: 900, currency: 'EUR' },
    icon: '💻',
    color: 'from-blue-500 to-indigo-600',
  },
  {
    id: 'public-speaking',
    name: 'Public Speaking Boost',
    description: 'Speech-crafting workshop, video rehearsals and peer-to-peer feedback',
    goal: 'DELIVERABLES: (1) Complete presentation outline with storytelling framework, key messages, and audience engagement strategies, (2) Slide deck template with visual design guidelines and speaker notes, (3) Speech practice recordings with weekly improvement analysis and feedback integration, (4) Body language and voice training exercises with practice schedules, (5) Q&A preparation with anticipated questions and structured response frameworks, (6) Speaking opportunity research with event applications and pitch templates',
    budget: { max_amount: 550, currency: 'EUR' },
    icon: '🎤',
    color: 'from-red-500 to-pink-600',
  },
  {
    id: 'digital-minimalism',
    name: 'Digital Minimalism Reset',
    description: '30-day challenge to reduce screen-time and reorganize devices/notifications',
    goal: 'DELIVERABLES: (1) Digital audit report with current usage patterns, time-wasting apps identification, and productivity opportunities, (2) Custom app organization system with essential apps only, notification settings optimization, and focus modes setup, (3) 30-day digital detox challenge with daily activities, progress tracking, and accountability measures, (4) Alternative activity list for device-free time including hobbies, exercise, reading, and social activities, (5) Productivity system with time-blocking, deep work sessions, and distraction-free work environment, (6) Long-term maintenance plan with weekly reviews and relapse prevention strategies',
    budget: { max_amount: 350, currency: 'EUR' },
    icon: '📱',
    color: 'from-gray-500 to-gray-700',
  },
  {
  id: 'outbound-mailup',
  name: 'B2B Outbound Sales Lists',
  description: 'Creation and qualification of prospect lists for MailUp outbound campaigns',
  goal: 'DELIVERABLES: (1) Qualified database of 500+ ICP contacts (CMO/CTO from European SaaS companies) with LinkedIn profiles, company details, and contact verification, (2) Three complete email sequences (cold outreach, nurture, follow-up) with A/B test variants for subject lines and CTAs, (3) HubSpot import-ready CSV with all contact data and sequence assignments, (4) Competitor analysis of successful outbound campaigns in SaaS industry, (5) Performance tracking dashboard template for monitoring campaign results, (6) Sales script templates and objection handling guides for follow-up calls',
  budget: { max_amount: 1000, currency: 'EUR' },
  icon: '📧',
  color: 'from-rose-500 to-pink-600',
},
    {
  id: 'abm-target-accounts',
  name: 'ABM Target Accounts',
  description: 'Identification and engagement of 100 ideal enterprise accounts with multi-channel outreach (email, LinkedIn, calls)',
  goal: 'DELIVERABLES: (1) Target account database of 100 enterprise companies with detailed company profiles, decision-maker mapping, and buying signals, (2) Account-specific outreach strategies for each account with personalized messaging and content recommendations, (3) Multi-channel engagement playbook covering LinkedIn, email, phone, and direct mail tactics, (4) Sales collateral package with case studies, ROI calculators, and demo scripts tailored for enterprise prospects, (5) Account scoring model and qualification criteria, (6) Pipeline tracking dashboard template with deal stages and forecasting tools',
  budget: { max_amount: 1200, currency: 'EUR' },
  icon: '🎯',
  color: 'from-indigo-500 to-violet-600',
},
{
  id: 'partner-prospecting',
  name: 'Channel Partner Prospecting',
  description: 'Build partner pipeline (agencies, resellers) for MailUp in the DACH market',
  goal: 'DELIVERABLES: (1) Partner prospect database of qualified agencies/resellers in DACH region with company profiles, services offered, and client portfolio analysis, (2) Partner recruitment kit including pitch deck, commission structure, training materials, and certification requirements, (3) Partner onboarding process with step-by-step checklist, training schedule, and performance milestones, (4) Co-marketing campaign templates and joint sales materials for new partners, (5) Partner portal setup guide with resources, leads distribution system, and performance tracking, (6) Quarterly partner review template with KPIs and growth planning framework',
  budget: { max_amount: 1500, currency: 'EUR' },
  icon: '🤝',
  color: 'from-emerald-500 to-teal-600',
},
{
  id: 'webinar-funnel',
  name: 'Webinar Demand Gen',
  description: 'Educational webinar organization and lead nurturing with MailUp email sequences',
  goal: 'DELIVERABLES: (1) Complete webinar strategy with educational topics, speaker recommendations, and promotional timeline, (2) Landing page optimization with registration forms, A/B tested headlines, and conversion tracking setup, (3) Email marketing sequences for promotion (pre-event), nurturing (post-event), and follow-up campaigns with automated scoring, (4) Webinar content package including slide templates, interactive polls, Q&A frameworks, and call-to-action strategies, (5) Lead qualification system with scoring criteria and handoff process to sales team, (6) Performance analytics dashboard for tracking registration sources, attendance rates, and conversion funnels',
  budget: { max_amount: 800, currency: 'EUR' },
  icon: '🎥',
  color: 'from-cyan-500 to-sky-600',
},
{
  id: 'customer-expansion',
  name: 'Customer Expansion Play',
  description: 'Active customer segmentation and automated upsell/cross-sell campaigns',
  goal: 'DELIVERABLES: (1) Customer segmentation analysis identifying high-value expansion opportunities with usage patterns, contract details, and growth potential scoring, (2) Automated upsell/cross-sell campaign workflows with trigger-based emails, product recommendations, and pricing tiers, (3) Customer success playbook with health scoring, renewal strategies, and expansion conversation scripts, (4) Personalized expansion proposals template with ROI calculations and implementation frameworks, (5) A/B tested email sequences for different customer segments and product combinations, (6) Revenue expansion tracking dashboard with ARPU trends, expansion rates, and churn risk indicators',
  budget: { max_amount: 700, currency: 'EUR' },
  icon: '📈',
  color: 'from-green-500 to-lime-600',
},
];

// Component for suggested project card
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
  const [activeTab, setActiveTab] = useState('existing'); // 'existing' or 'suggested'
  
  // Mock user ID for development
  const mockUserId = '123e4567-e89b-12d3-a456-426614174000';
  
  // 📊 Quota monitoring for home page
  const { quotaStatus, getUsagePercentage } = useQuotaMonitor({
    enableWebSocket: true,
    showNotifications: false // We'll use the banner notification instead
  });
  
  useEffect(() => {
    const fetchWorkspaces = async () => {
      try {
        setLoading(true);
        const data = await api.workspaces.list(mockUserId);
        setWorkspaces(data);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch workspaces:', err);
        setError('Unable to load projects. Please try again later.');
        // For testing, show mock data
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
    // Navigate directly to conversation interface, bypassing intermediate redirect
    router.push(`/projects/${id}/conversation`);
  };
  
  const handleSuggestedProjectClick = (project: typeof suggestedProjects[number]) => {
    // Save template data in localStorage to retrieve it on the creation page
    localStorage.setItem('projectTemplate', JSON.stringify({
      name: project.name,
      description: project.description,
      goal: project.goal,
      budget: project.budget
    }));
    
    // Navigate to the new project creation page
    router.push('/projects/new');
  };
  
  return (
    <div className="container mx-auto">
      {/* Quota Alert Banner - Inline for home page */}
      <QuotaNotification
        position="inline"
        showUsageBar={true}
        autoRefresh={true}
      />
      
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold">Your Projects</h1>
        <Link href="/projects/new" className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition">
          New Project
        </Link>
      </div>
      
      {/* Tab Navigation */}
      <div className="flex border-b border-gray-200 mb-6">
        <button
          className={`px-4 py-2 font-medium text-sm ${activeTab === 'existing' ? 'text-indigo-600 border-b-2 border-indigo-500' : 'text-gray-500 hover:text-gray-700'}`}
          onClick={() => setActiveTab('existing')}
        >
          Your Projects
        </button>
        <button
          className={`px-4 py-2 font-medium text-sm ${activeTab === 'suggested' ? 'text-indigo-600 border-b-2 border-indigo-500' : 'text-gray-500 hover:text-gray-700'}`}
          onClick={() => setActiveTab('suggested')}
        >
          Suggested Projects
        </button>
      </div>
      
      {/* Tab Content */}
      {activeTab === 'existing' && (
        <>
          {loading ? (
            <div className="text-center py-10">
              <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-indigo-600 border-r-transparent"></div>
              <p className="mt-2 text-gray-600">Loading projects...</p>
            </div>
          ) : error ? (
            <div className="bg-red-50 text-red-700 p-4 rounded-md mb-6">
              {error}
            </div>
          ) : workspaces.length === 0 ? (
            <div className="text-center py-10 bg-white rounded-lg shadow-sm">
              <h3 className="text-lg font-medium text-gray-600">No projects found</h3>
              <p className="text-gray-500 mt-2">Start by creating your first project or choose one of our suggested templates</p>
              <div className="mt-4 flex gap-3 justify-center">
                <Link href="/projects/new" className="inline-block px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition">
                  Create Project
                </Link>
                <button 
                  onClick={() => setActiveTab('suggested')} 
                  className="inline-block px-4 py-2 bg-green-600 text-white rounded-md text-sm hover:bg-green-700 transition"
                >
                  Suggested Projects
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
                      workspace.status === 'processing_tasks' ? 'bg-blue-100 text-blue-800' :
                      workspace.status === 'paused' ? 'bg-yellow-100 text-yellow-800' :
                      workspace.status === 'completed' ? 'bg-gray-100 text-gray-800' :
                      workspace.status === 'auto_recovering' ? 'bg-orange-100 text-orange-800' :
                      workspace.status === 'degraded_mode' ? 'bg-yellow-100 text-yellow-800' :
                      workspace.status === 'error' ? 'bg-red-100 text-red-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {workspace.status === 'active' ? 'Active' :
                       workspace.status === 'created' ? 'Created' :
                       workspace.status === 'processing_tasks' ? 'Processing' :
                       workspace.status === 'paused' ? 'Paused' :
                       workspace.status === 'completed' ? 'Completed' :
                       workspace.status === 'auto_recovering' ? 'Auto Recovering' :
                       workspace.status === 'degraded_mode' ? 'Degraded Mode' :
                       workspace.status === 'error' ? 'Error' :
                       workspace.status}
                    </span>
                  </div>
                  
                  <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                    {workspace.description || 'No description'}
                  </p>
                  
                  <div className="border-t pt-4 mt-4">
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <p className="text-gray-500">Goal</p>
                        <p className="font-medium text-gray-800 truncate">
                          {workspace.goal || 'Not specified'}
                        </p>
                      </div>
                      <div>
                        <p className="text-gray-500">Budget</p>
                        <p className="font-medium text-gray-800">
                          {workspace.budget && workspace.budget.max_amount && workspace.budget.currency
                            ? `${workspace.budget.max_amount} ${workspace.budget.currency}`
                            : 'Not specified'}
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
              Select one of the suggested projects to start quickly. All details will be pre-filled automatically.
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