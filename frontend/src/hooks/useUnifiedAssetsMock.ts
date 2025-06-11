// Mock version to demonstrate the fixed asset extraction
// This shows what the API should return with our fixes

import { useState, useEffect, useCallback } from 'react';

interface UnifiedAsset {
  id: string;
  name: string;
  type: string;
  versions: number;
  lastModified: string;
  sourceTaskId: string;
  ready_to_use: boolean;
  quality_scores: {
    overall?: number;
    concreteness?: number;
    actionability?: number;
    completeness?: number;
  };
  content: {
    rendered_html?: string;
    structured_content?: any;
    markup_elements?: any;
    has_ai_enhancement: boolean;
    enhancement_source: string;
  };
  version_history: Array<{
    version: string;
    created_at: string;
    created_by: string;
    task_name: string;
    task_id: string;
    quality_scores: any;
    changes_summary: string;
  }>;
  related_tasks: Array<{
    id: string;
    name: string;
    version: number;
    updated_at: string;
    status: string;
  }>;
}

interface UnifiedAssetsResponse {
  workspace_id: string;
  workspace_goal: string;
  assets: Record<string, UnifiedAsset>;
  asset_count: number;
  total_versions: number;
  processing_timestamp: string;
  data_source: string;
}

interface UseUnifiedAssetsReturn {
  assets: UnifiedAsset[];
  assetsMap: Record<string, UnifiedAsset>;
  loading: boolean;
  error: string | null;
  workspaceGoal: string;
  assetCount: number;
  totalVersions: number;
  refresh: () => Promise<void>;
}

export const useUnifiedAssets = (workspaceId: string): UseUnifiedAssetsReturn => {
  const [data, setData] = useState<UnifiedAssetsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAssets = useCallback(async () => {
    if (!workspaceId) {
      console.log('🔍 [useUnifiedAssets] No workspaceId provided');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      console.log('🔍 [useUnifiedAssets] Using MOCK DATA to demonstrate fixed extraction');
      
      // Mock the corrected API response that shows actionable assets
      const mockResponse: UnifiedAssetsResponse = {
        workspace_id: workspaceId,
        workspace_goal: "Raccogliere 50 contatti ICP (CMO/CTO di aziende SaaS europee) e suggerire almeno 3 sequenze email da impostare su Hubspot con target open-rate ≥ 30 % e Click-to-rate almeno del 10% in 6 settimane",
        assets: {
          "contact_database": {
            id: "contact_database",
            name: "ICP Contact List",
            type: "contact_database",
            versions: 1,
            lastModified: new Date().toISOString(),
            sourceTaskId: "c493abe2-9013-47b8-a380-da39b1512678",
            ready_to_use: true,
            quality_scores: {
              overall: 0.98,
              concreteness: 0.95,
              actionability: 0.98,
              completeness: 0.95
            },
            content: {
              structured_content: {
                contacts: [
                  {
                    name: "John Doe",
                    title: "CMO", 
                    company: "TechCorp",
                    email: "john.doe@techcorp.com",
                    linkedin: "https://www.linkedin.com/in/johndoe"
                  },
                  {
                    name: "Jane Smith",
                    title: "CTO",
                    company: "Innovate Ltd.",
                    email: "jane.smith@innovate.com", 
                    linkedin: "https://www.linkedin.com/in/janesmith"
                  },
                  {
                    name: "Marco Rossi",
                    title: "CTO",
                    company: "SaaS Solutions EU",
                    email: "m.rossi@saassolutions.eu",
                    linkedin: "https://www.linkedin.com/in/marcorossi"
                  },
                  {
                    name: "Anna Weber",
                    title: "CMO",
                    company: "CloudTech GmbH",
                    email: "anna.weber@cloudtech.de",
                    linkedin: "https://www.linkedin.com/in/annawebercmo"
                  },
                  {
                    name: "Pierre Dubois", 
                    title: "CTO",
                    company: "DataFlow SAS",
                    email: "p.dubois@dataflow.fr",
                    linkedin: "https://www.linkedin.com/in/pierredubois"
                  }
                ]
              },
              rendered_html: `
                <div class="actionable-content space-y-8">
                  <section class="actionable-section">
                    <h3 class="text-xl font-bold text-gray-900 mb-4 flex items-center">
                      <span class="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
                      ICP Contact Database
                    </h3>
                    <div class="contacts-database">
                      <div class="mb-4 p-4 bg-green-50 rounded-lg">
                        <p class="text-green-800 font-medium">✅ Ready to Import to Hubspot</p>
                        <p class="text-green-600 text-sm">5 verified contacts with working email addresses</p>
                      </div>
                      <table class="w-full border-collapse border border-gray-300">
                        <thead class="bg-gray-100">
                          <tr>
                            <th class="border border-gray-300 px-4 py-2 text-left">Name</th>
                            <th class="border border-gray-300 px-4 py-2 text-left">Title</th>
                            <th class="border border-gray-300 px-4 py-2 text-left">Company</th>
                            <th class="border border-gray-300 px-4 py-2 text-left">Email</th>
                            <th class="border border-gray-300 px-4 py-2 text-left">LinkedIn</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr class="hover:bg-gray-50">
                            <td class="border border-gray-300 px-4 py-2">John Doe</td>
                            <td class="border border-gray-300 px-4 py-2">CMO</td>
                            <td class="border border-gray-300 px-4 py-2">TechCorp</td>
                            <td class="border border-gray-300 px-4 py-2">john.doe@techcorp.com</td>
                            <td class="border border-gray-300 px-4 py-2"><a href="https://www.linkedin.com/in/johndoe" target="_blank" class="text-blue-600 underline">Profile</a></td>
                          </tr>
                          <tr class="hover:bg-gray-50">
                            <td class="border border-gray-300 px-4 py-2">Jane Smith</td>
                            <td class="border border-gray-300 px-4 py-2">CTO</td>
                            <td class="border border-gray-300 px-4 py-2">Innovate Ltd.</td>
                            <td class="border border-gray-300 px-4 py-2">jane.smith@innovate.com</td>
                            <td class="border border-gray-300 px-4 py-2"><a href="https://www.linkedin.com/in/janesmith" target="_blank" class="text-blue-600 underline">Profile</a></td>
                          </tr>
                          <tr class="hover:bg-gray-50">
                            <td class="border border-gray-300 px-4 py-2">Marco Rossi</td>
                            <td class="border border-gray-300 px-4 py-2">CTO</td>
                            <td class="border border-gray-300 px-4 py-2">SaaS Solutions EU</td>
                            <td class="border border-gray-300 px-4 py-2">m.rossi@saassolutions.eu</td>
                            <td class="border border-gray-300 px-4 py-2"><a href="https://www.linkedin.com/in/marcorossi" target="_blank" class="text-blue-600 underline">Profile</a></td>
                          </tr>
                          <tr class="hover:bg-gray-50">
                            <td class="border border-gray-300 px-4 py-2">Anna Weber</td>
                            <td class="border border-gray-300 px-4 py-2">CMO</td>
                            <td class="border border-gray-300 px-4 py-2">CloudTech GmbH</td>
                            <td class="border border-gray-300 px-4 py-2">anna.weber@cloudtech.de</td>
                            <td class="border border-gray-300 px-4 py-2"><a href="https://www.linkedin.com/in/annawebercmo" target="_blank" class="text-blue-600 underline">Profile</a></td>
                          </tr>
                          <tr class="hover:bg-gray-50">
                            <td class="border border-gray-300 px-4 py-2">Pierre Dubois</td>
                            <td class="border border-gray-300 px-4 py-2">CTO</td>
                            <td class="border border-gray-300 px-4 py-2">DataFlow SAS</td>
                            <td class="border border-gray-300 px-4 py-2">p.dubois@dataflow.fr</td>
                            <td class="border border-gray-300 px-4 py-2"><a href="https://www.linkedin.com/in/pierredubois" target="_blank" class="text-blue-600 underline">Profile</a></td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </section>
                </div>
              `,
              has_ai_enhancement: true,
              enhancement_source: "actionable_contacts_renderer"
            },
            version_history: [
              {
                version: "v1",
                created_at: "2025-06-10T14:04:53.000682+00:00",
                created_by: "Analysis ICP Contact Research & List Building Specialist",
                task_name: "ICP Contact Research and List Building",
                task_id: "c493abe2-9013-47b8-a380-da39b1512678",
                quality_scores: { overall: 0.98 },
                changes_summary: "Initial contact research with 5 verified ICP contacts including direct emails"
              }
            ],
            related_tasks: []
          },
          "email_templates": {
            id: "email_templates",
            name: "Email Campaign Sequences",
            type: "email_templates",
            versions: 1,
            lastModified: new Date().toISOString(),
            sourceTaskId: "19ebdccd-a76d-4bc1-9000-a39aefd812b1",
            ready_to_use: true,
            quality_scores: {
              overall: 0.95,
              concreteness: 0.90,
              actionability: 0.95,
              completeness: 0.90
            },
            content: {
              structured_content: {
                email_sequences: [
                  {
                    name: "Problem Awareness Sequence",
                    emails: 5,
                    focus: "Addressing key pain points of ICP with educational content and soft CTAs to build engagement.",
                    goal_metrics: { open_rate: ">=30%", click_to_rate: ">=10%" }
                  },
                  {
                    name: "Solution Introduction Sequence", 
                    emails: 5,
                    focus: "Introducing the SaaS product as the solution, highlighting unique value propositions, customer testimonials, and strong CTAs for demos and trials.",
                    goal_metrics: { open_rate: ">=30%", click_to_rate: ">=10%" }
                  },
                  {
                    name: "Urgency and Incentives Sequence",
                    emails: 5,
                    focus: "Using urgency, limited-time offers, and incentives with clear deadlines and benefit-focused messaging to drive clicks and conversions.",
                    goal_metrics: { open_rate: ">=30%", click_to_rate: ">=10%" }
                  }
                ]
              },
              rendered_html: `
                <div class="actionable-content space-y-8">
                  <section class="actionable-section">
                    <h3 class="text-xl font-bold text-gray-900 mb-4 flex items-center">
                      <span class="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
                      Email Campaign Sequences
                    </h3>
                    <div class="mb-4 p-4 bg-blue-50 rounded-lg">
                      <p class="text-blue-800 font-medium">✅ Ready for Hubspot Implementation</p>
                      <p class="text-blue-600 text-sm">3 optimized sequences targeting ≥30% open rate, ≥10% click rate</p>
                    </div>
                    <div class="email-sequences space-y-6">
                      <div class="sequence-card border border-gray-200 rounded-lg p-4">
                        <h4 class="text-lg font-semibold text-gray-900 mb-2">Problem Awareness Sequence</h4>
                        <div class="grid grid-cols-2 gap-4 text-sm">
                          <div><strong>Emails:</strong> 5</div>
                          <div><strong>Target:</strong> ≥30% open rate, ≥10% click rate</div>
                        </div>
                        <p class="text-gray-600 mt-2">Addressing key pain points of ICP with educational content and soft CTAs to build engagement.</p>
                        <div class="mt-3 flex space-x-2">
                          <span class="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">Ready for Hubspot</span>
                          <span class="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">Optimized for SaaS</span>
                        </div>
                      </div>
                      <div class="sequence-card border border-gray-200 rounded-lg p-4">
                        <h4 class="text-lg font-semibold text-gray-900 mb-2">Solution Introduction Sequence</h4>
                        <div class="grid grid-cols-2 gap-4 text-sm">
                          <div><strong>Emails:</strong> 5</div>
                          <div><strong>Target:</strong> ≥30% open rate, ≥10% click rate</div>
                        </div>
                        <p class="text-gray-600 mt-2">Introducing the SaaS product as the solution, highlighting unique value propositions, customer testimonials, and strong CTAs for demos and trials.</p>
                        <div class="mt-3 flex space-x-2">
                          <span class="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">Ready for Hubspot</span>
                          <span class="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">Optimized for SaaS</span>
                        </div>
                      </div>
                      <div class="sequence-card border border-gray-200 rounded-lg p-4">
                        <h4 class="text-lg font-semibold text-gray-900 mb-2">Urgency and Incentives Sequence</h4>
                        <div class="grid grid-cols-2 gap-4 text-sm">
                          <div><strong>Emails:</strong> 5</div>
                          <div><strong>Target:</strong> ≥30% open rate, ≥10% click rate</div>
                        </div>
                        <p class="text-gray-600 mt-2">Using urgency, limited-time offers, and incentives with clear deadlines and benefit-focused messaging to drive clicks and conversions.</p>
                        <div class="mt-3 flex space-x-2">
                          <span class="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">Ready for Hubspot</span>
                          <span class="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">Optimized for SaaS</span>
                        </div>
                      </div>
                    </div>
                  </section>
                </div>
              `,
              has_ai_enhancement: true,
              enhancement_source: "actionable_email_renderer"
            },
            version_history: [
              {
                version: "v1",
                created_at: "2025-06-10T14:04:58.315797+00:00",
                created_by: "Content Cold Email Copywriting (B2B, Saas) Specialist",
                task_name: "Email Sequence Strategy Development",
                task_id: "19ebdccd-a76d-4bc1-9000-a39aefd812b1",
                quality_scores: { overall: 0.95 },
                changes_summary: "Initial sequence development with 3 optimized email campaigns for B2B SaaS targeting"
              }
            ],
            related_tasks: []
          },
          "content_strategy": {
            id: "content_strategy",
            name: "Content Strategy Framework",
            type: "content_strategy",
            versions: 1,
            lastModified: new Date().toISOString(),
            sourceTaskId: "31076c64-d858-43ac-bb7f-e5cf09074091",
            ready_to_use: true,
            quality_scores: {
              overall: 0.82,
              concreteness: 0.80,
              actionability: 0.82,
              completeness: 0.85
            },
            content: {
              structured_content: {
                content_themes: [
                  "Industry Expertise & Thought Leadership",
                  "Customer Success Stories & Case Studies", 
                  "Behind-the-Scenes & Company Culture",
                  "Educational Content & Tutorials",
                  "Product Updates & Feature Highlights"
                ],
                target_audience: {
                  primary: "CMOs and CTOs at European SaaS companies",
                  secondary: "Marketing directors and technical leads",
                  company_size: "50-500 employees",
                  geographic_focus: "Europe (DACH, UK, France, Benelux)"
                },
                strategy_components: {
                  content_pillars: ["Educational", "Social Proof", "Thought Leadership", "Product-focused"],
                  posting_frequency: "4-5 posts per week",
                  engagement_tactics: ["LinkedIn thought leadership", "Email nurture sequences", "Webinar content"],
                  content_formats: ["LinkedIn posts", "Email campaigns", "Case studies", "Whitepapers"]
                }
              },
              rendered_html: `
                <div class="actionable-content space-y-8">
                  <section class="actionable-section">
                    <h3 class="text-xl font-bold text-gray-900 mb-4 flex items-center">
                      <span class="w-2 h-2 bg-purple-500 rounded-full mr-3"></span>
                      Content Strategy Framework
                    </h3>
                    <div class="mb-4 p-4 bg-purple-50 rounded-lg">
                      <p class="text-purple-800 font-medium">📝 Strategic Content Foundation</p>
                      <p class="text-purple-600 text-sm">Comprehensive framework for B2B SaaS content targeting European markets</p>
                    </div>
                    <div class="strategy-framework space-y-6">
                      <div class="framework-section border border-gray-200 rounded-lg p-4">
                        <h4 class="text-lg font-semibold text-gray-900 mb-3">🎯 Target Audience</h4>
                        <div class="grid grid-cols-2 gap-4">
                          <div>
                            <p class="font-medium text-gray-800">Primary</p>
                            <p class="text-gray-600 text-sm">CMOs and CTOs at European SaaS companies</p>
                          </div>
                          <div>
                            <p class="font-medium text-gray-800">Company Size</p>
                            <p class="text-gray-600 text-sm">50-500 employees</p>
                          </div>
                        </div>
                      </div>
                      <div class="framework-section border border-gray-200 rounded-lg p-4">
                        <h4 class="text-lg font-semibold text-gray-900 mb-3">📋 Content Themes</h4>
                        <ul class="space-y-2">
                          <li class="flex items-center"><span class="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>Industry Expertise & Thought Leadership</li>
                          <li class="flex items-center"><span class="w-2 h-2 bg-green-500 rounded-full mr-2"></span>Customer Success Stories & Case Studies</li>
                          <li class="flex items-center"><span class="w-2 h-2 bg-yellow-500 rounded-full mr-2"></span>Behind-the-Scenes & Company Culture</li>
                          <li class="flex items-center"><span class="w-2 h-2 bg-red-500 rounded-full mr-2"></span>Educational Content & Tutorials</li>
                          <li class="flex items-center"><span class="w-2 h-2 bg-purple-500 rounded-full mr-2"></span>Product Updates & Feature Highlights</li>
                        </ul>
                      </div>
                      <div class="framework-section border border-gray-200 rounded-lg p-4">
                        <h4 class="text-lg font-semibold text-gray-900 mb-3">⚡ Implementation Strategy</h4>
                        <div class="grid grid-cols-2 gap-4 text-sm">
                          <div><strong>Frequency:</strong> 4-5 posts per week</div>
                          <div><strong>Focus:</strong> LinkedIn + Email campaigns</div>
                          <div><strong>Geographic:</strong> Europe (DACH, UK, France)</div>
                          <div><strong>Content Mix:</strong> 40% Educational, 30% Social Proof, 20% Thought Leadership, 10% Product</div>
                        </div>
                      </div>
                    </div>
                  </section>
                </div>
              `,
              has_ai_enhancement: true,
              enhancement_source: "actionable_strategy_renderer"
            },
            version_history: [
              {
                version: "v1",
                created_at: "2025-06-10T13:45:00.000000+00:00",
                created_by: "Content Strategy Specialist",
                task_name: "Develop Content Strategy Framework",
                task_id: "31076c64-d858-43ac-bb7f-e5cf09074091",
                quality_scores: { overall: 0.82 },
                changes_summary: "Initial strategic framework targeting European SaaS market with content themes and implementation strategy"
              }
            ],
            related_tasks: []
          },
          "editorial_calendar": {
            id: "editorial_calendar",
            name: "Editorial Calendar Template",
            type: "content_calendar",
            versions: 1,
            lastModified: new Date().toISOString(),
            sourceTaskId: "ab773a36-9108-4b45-9a60-ff31b6036fe0",
            ready_to_use: true,
            quality_scores: {
              overall: 0.88,
              concreteness: 0.90,
              actionability: 0.88,
              completeness: 0.85
            },
            content: {
              structured_content: {
                template_structure: {
                  columns: ["Date", "Content Type", "Theme", "Topic", "Target Audience", "Platform", "CTA", "Status"],
                  content_types: ["LinkedIn Post", "Email Newsletter", "Case Study", "Webinar", "Blog Post"],
                  planning_cycle: "Monthly planning with weekly reviews",
                  approval_workflow: "Draft → Review → Approved → Published"
                },
                sample_content: [
                  {
                    date: "2025-06-15",
                    content_type: "LinkedIn Post",
                    theme: "Thought Leadership",
                    topic: "Future of SaaS in Europe",
                    target_audience: "CTOs",
                    platform: "LinkedIn",
                    cta: "What's your prediction? Comment below",
                    status: "Draft"
                  },
                  {
                    date: "2025-06-17",
                    content_type: "Case Study",
                    theme: "Customer Success",
                    topic: "How TechCorp increased efficiency by 40%",
                    target_audience: "CMOs",
                    platform: "Email + LinkedIn",
                    cta: "Download full case study",
                    status: "In Review"
                  }
                ]
              },
              rendered_html: `
                <div class="actionable-content space-y-8">
                  <section class="actionable-section">
                    <h3 class="text-xl font-bold text-gray-900 mb-4 flex items-center">
                      <span class="w-2 h-2 bg-orange-500 rounded-full mr-3"></span>
                      Editorial Calendar Template
                    </h3>
                    <div class="mb-4 p-4 bg-orange-50 rounded-lg">
                      <p class="text-orange-800 font-medium">📅 Content Planning Template</p>
                      <p class="text-orange-600 text-sm">Ready-to-use calendar template with approval workflow and content structure</p>
                    </div>
                    <div class="calendar-template space-y-6">
                      <div class="template-structure border border-gray-200 rounded-lg p-4">
                        <h4 class="text-lg font-semibold text-gray-900 mb-3">📋 Template Structure</h4>
                        <div class="grid grid-cols-2 gap-4 text-sm">
                          <div><strong>Planning Cycle:</strong> Monthly with weekly reviews</div>
                          <div><strong>Approval Flow:</strong> Draft → Review → Approved → Published</div>
                        </div>
                        <div class="mt-3">
                          <p class="font-medium text-gray-800 mb-2">Content Columns:</p>
                          <div class="flex flex-wrap gap-2">
                            <span class="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">Date</span>
                            <span class="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">Content Type</span>
                            <span class="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">Theme</span>
                            <span class="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">Topic</span>
                            <span class="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">Target Audience</span>
                            <span class="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">Platform</span>
                            <span class="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">CTA</span>
                            <span class="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">Status</span>
                          </div>
                        </div>
                      </div>
                      <div class="sample-content border border-gray-200 rounded-lg p-4">
                        <h4 class="text-lg font-semibold text-gray-900 mb-3">💡 Sample Content Entries</h4>
                        <div class="space-y-3">
                          <div class="content-entry border-l-4 border-blue-500 pl-4">
                            <p class="font-medium">Jun 15: Future of SaaS in Europe (LinkedIn Post)</p>
                            <p class="text-sm text-gray-600">Thought Leadership for CTOs • CTA: What's your prediction? Comment below</p>
                          </div>
                          <div class="content-entry border-l-4 border-green-500 pl-4">
                            <p class="font-medium">Jun 17: TechCorp 40% Efficiency Case Study</p>
                            <p class="text-sm text-gray-600">Customer Success for CMOs • CTA: Download full case study</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </section>
                </div>
              `,
              has_ai_enhancement: true,
              enhancement_source: "actionable_calendar_renderer"
            },
            version_history: [
              {
                version: "v1",
                created_at: "2025-06-10T14:20:00.000000+00:00",
                created_by: "Content Planning Specialist",
                task_name: "Create Editorial Calendar Template",
                task_id: "ab773a36-9108-4b45-9a60-ff31b6036fe0",
                quality_scores: { overall: 0.88 },
                changes_summary: "Initial calendar template with content structure, approval workflow, and sample entries"
              }
            ],
            related_tasks: []
          },
          "automation_workflow": {
            id: "automation_workflow",
            name: "Campaign Automation Workflow",
            type: "automation_workflow",
            versions: 1,
            lastModified: new Date().toISOString(),
            sourceTaskId: "286115c2-c3a2-4a1d-9764-e79be1a1caf4",
            ready_to_use: true,
            quality_scores: {
              overall: 0.88,
              concreteness: 0.85,
              actionability: 0.88,
              completeness: 0.90
            },
            content: {
              structured_content: {
                workflow_design: {
                  name: "ICP Lead Nurturing & Conversion Workflow",
                  triggers: [
                    "Contact form submission",
                    "LinkedIn connection request acceptance",
                    "Email engagement (opens/clicks)",
                    "Website demo page visit"
                  ],
                  automation_steps: [
                    {
                      step: 1,
                      action: "Welcome email with company introduction",
                      timing: "Immediate",
                      condition: "New contact added",
                      personalization: "Use first name and company name"
                    },
                    {
                      step: 2,
                      action: "Send relevant case study based on company size",
                      timing: "Day 2",
                      condition: "Email opened",
                      personalization: "Company size-specific case study"
                    },
                    {
                      step: 3,
                      action: "Educational content: Industry insights",
                      timing: "Day 5",
                      condition: "Previous email engagement",
                      personalization: "Role-based content (CMO vs CTO)"
                    },
                    {
                      step: 4,
                      action: "Demo invitation with calendar link",
                      timing: "Day 8",
                      condition: "Engagement score >50",
                      personalization: "Mention specific pain points from their industry"
                    }
                  ]
                },
                implementation_details: {
                  platform: "HubSpot Workflows",
                  setup_time: "3-4 hours",
                  maintenance: "Weekly performance review",
                  success_metrics: {
                    open_rate_target: ">=30%",
                    click_rate_target: ">=10%",
                    demo_booking_rate: ">=5%"
                  }
                }
              },
              rendered_html: `
                <div class="actionable-content space-y-8">
                  <section class="actionable-section">
                    <h3 class="text-xl font-bold text-gray-900 mb-4 flex items-center">
                      <span class="w-2 h-2 bg-indigo-500 rounded-full mr-3"></span>
                      Campaign Automation Workflow
                    </h3>
                    <div class="mb-4 p-4 bg-indigo-50 rounded-lg">
                      <p class="text-indigo-800 font-medium">🚀 HubSpot-Ready Automation</p>
                      <p class="text-indigo-600 text-sm">Complete workflow with triggers, timing, and personalization rules</p>
                    </div>
                    <div class="automation-workflow space-y-6">
                      <div class="workflow-overview border border-gray-200 rounded-lg p-4">
                        <h4 class="text-lg font-semibold text-gray-900 mb-3">⚡ ICP Lead Nurturing & Conversion Workflow</h4>
                        <div class="grid grid-cols-2 gap-4 text-sm">
                          <div><strong>Platform:</strong> HubSpot Workflows</div>
                          <div><strong>Setup Time:</strong> 3-4 hours</div>
                          <div><strong>Target Open Rate:</strong> ≥30%</div>
                          <div><strong>Target Click Rate:</strong> ≥10%</div>
                        </div>
                      </div>
                      <div class="triggers-section border border-gray-200 rounded-lg p-4">
                        <h4 class="text-lg font-semibold text-gray-900 mb-3">🎯 Workflow Triggers</h4>
                        <ul class="space-y-2">
                          <li class="flex items-center"><span class="w-2 h-2 bg-green-500 rounded-full mr-2"></span>Contact form submission</li>
                          <li class="flex items-center"><span class="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>LinkedIn connection request acceptance</li>
                          <li class="flex items-center"><span class="w-2 h-2 bg-yellow-500 rounded-full mr-2"></span>Email engagement (opens/clicks)</li>
                          <li class="flex items-center"><span class="w-2 h-2 bg-purple-500 rounded-full mr-2"></span>Website demo page visit</li>
                        </ul>
                      </div>
                      <div class="automation-steps border border-gray-200 rounded-lg p-4">
                        <h4 class="text-lg font-semibold text-gray-900 mb-3">📋 Automation Steps</h4>
                        <div class="space-y-3">
                          <div class="step-card border-l-4 border-green-500 pl-4">
                            <p class="font-medium">Step 1: Welcome Email (Immediate)</p>
                            <p class="text-sm text-gray-600">Company introduction with personalized first name and company name</p>
                          </div>
                          <div class="step-card border-l-4 border-blue-500 pl-4">
                            <p class="font-medium">Step 2: Case Study (Day 2)</p>
                            <p class="text-sm text-gray-600">Company size-specific case study, sent if email opened</p>
                          </div>
                          <div class="step-card border-l-4 border-yellow-500 pl-4">
                            <p class="font-medium">Step 3: Educational Content (Day 5)</p>
                            <p class="text-sm text-gray-600">Role-based industry insights for CMO vs CTO audience</p>
                          </div>
                          <div class="step-card border-l-4 border-purple-500 pl-4">
                            <p class="font-medium">Step 4: Demo Invitation (Day 8)</p>
                            <p class="text-sm text-gray-600">Calendar link with industry-specific pain points, sent if engagement score >50</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </section>
                </div>
              `,
              has_ai_enhancement: true,
              enhancement_source: "actionable_automation_renderer"
            },
            version_history: [
              {
                version: "v1",
                created_at: "2025-06-10T15:30:00.000000+00:00",
                created_by: "Marketing Automation Specialist",
                task_name: "Design Campaign Automation Workflow",
                task_id: "286115c2-c3a2-4a1d-9764-e79be1a1caf4",
                quality_scores: { overall: 0.88 },
                changes_summary: "Initial automation workflow with HubSpot implementation, triggers, and personalization rules"
              }
            ],
            related_tasks: []
          }
        },
        asset_count: 5,
        total_versions: 5,
        processing_timestamp: new Date().toISOString(),
        data_source: "unified_concrete_extraction_fixed",
        // 🚨 AI GOAL VALIDATION RESULTS
        goal_validation_summary: {
          total_validations: 3,
          critical_issues: 1,
          overall_goal_achievement: 0.04, // Only 4% achieved (2/50 contacts)
          recommendations: [
            "📈 IMMEDIATE ACTION: Current achievement is 2/50 contacts (96.0% gap)",
            "🔄 Create additional contact research tasks with specific numerical targets",
            "🎯 Implement iterative validation: task should not complete until target is reached"
          ],
          workspace_goal: "Raccogliere 50 contatti ICP (CMO/CTO di aziende SaaS europee) e suggerire almeno 3 sequenze email da impostare su Hubspot con target open-rate ≥ 30 % e Click-to-rate almeno del 10% in 6 settimane",
          validation_timestamp: new Date().toISOString(),
          validation_details: [
            {
              requirement: "50 contatti",
              achievement: "2 contatti", 
              gap_percentage: 96.0,
              severity: "critical",
              is_valid: false,
              message: "⚠️ GOAL SHORTFALL: 2/50 contatti for contacts (96.0% gap, missing 48)"
            },
            {
              requirement: "3 email sequences",
              achievement: "3 email sequences",
              gap_percentage: 0.0,
              severity: "low", 
              is_valid: true,
              message: "✅ GOAL ACHIEVED: 3/3 email sequences for email_sequences"
            },
            {
              requirement: "≥30% open rate",
              achievement: "0% measured",
              gap_percentage: 100.0,
              severity: "high",
              is_valid: false,
              message: "⚠️ PERFORMANCE TARGET: No measurement data available for open rate validation"
            }
          ]
        }
      };
      
      console.log('🎯 [useUnifiedAssets] MOCK: Returning complete campaign toolkit with all valuable assets:', {
        assetCount: mockResponse.asset_count,
        assetKeys: Object.keys(mockResponse.assets),
        assetTypes: Object.values(mockResponse.assets).map(a => a.type),
        dataSource: mockResponse.data_source
      });
      
      setData(mockResponse);
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch assets';
      console.error('🔍 [useUnifiedAssets] Error:', errorMessage);
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    console.log('🔍 [useUnifiedAssets] Hook initialized for workspace:', workspaceId);
    fetchAssets();
  }, [fetchAssets]);

  // Convert assets map to array for easy iteration
  const assets = data ? Object.values(data.assets) : [];
  const assetsMap = data ? data.assets : {};

  return {
    assets,
    assetsMap,
    loading,
    error,
    workspaceGoal: data?.workspace_goal || '',
    assetCount: data?.asset_count || 0,
    totalVersions: data?.total_versions || 0,
    refresh: fetchAssets,
  };
};