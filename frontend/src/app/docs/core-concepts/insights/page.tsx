'use client'

import React from 'react'
import Link from 'next/link'
import { ArrowLeft, Brain, Search, Edit, Trash2, RotateCcw, Users, CheckCircle, AlertTriangle, Sparkles, Database, History } from 'lucide-react'

export default function InsightsPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <Link 
              href="/docs"
              className="inline-flex items-center text-blue-600 hover:text-blue-800 transition-colors mb-4"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Documentation
            </Link>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">User Insights Management</h1>
            <p className="text-gray-600">Hybrid AI+Human knowledge management with intelligent categorization</p>
          </div>

          <div className="bg-white rounded-xl border p-8">
            {/* Overview */}
            <section className="mb-12">
              <div className="bg-purple-50 rounded-lg p-6 border border-purple-200 mb-6">
                <div className="flex items-center space-x-3">
                  <Brain className="w-6 h-6 text-purple-600" />
                  <div>
                    <h3 className="text-lg font-semibold text-purple-900">Hybrid AI+Human Knowledge System</h3>
                    <p className="text-purple-700 mt-1">
                      Complete user control over workspace knowledge insights, enhanced by AI-driven semantic 
                      categorization, with full CRUD operations, audit trails, and intelligent organization.
                    </p>
                  </div>
                </div>
              </div>

              <div className="prose prose-lg max-w-none">
                <p>
                  The User Insights Management System empowers users to create, organize, and manage knowledge 
                  insights within their workspace. Unlike pure AI systems, this provides complete human control 
                  while leveraging AI for intelligent categorization and content enhancement.
                </p>
              </div>
            </section>

            {/* Core Features */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                <Sparkles className="w-6 h-6 mr-3 text-indigo-600" />
                Core Features
              </h2>

              <div className="grid md:grid-cols-2 gap-6 mb-8">
                <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-6 border border-green-200">
                  <div className="flex items-center space-x-3 mb-4">
                    <Edit className="w-6 h-6 text-green-600" />
                    <h3 className="font-semibold text-green-900">Complete CRUD Operations</h3>
                  </div>
                  <ul className="text-sm text-green-800 space-y-2">
                    <li>• **Create**: Add insights with rich metadata</li>
                    <li>• **Read**: Search, filter, and browse knowledge</li>
                    <li>• **Update**: Edit content and categorization</li>
                    <li>• **Delete**: Soft delete with recovery options</li>
                  </ul>
                  <div className="mt-4 px-3 py-2 bg-green-200 rounded text-xs text-green-900">
                    <strong>User Control:</strong> 100% human oversight of all operations
                  </div>
                </div>

                <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-6 border border-blue-200">
                  <div className="flex items-center space-x-3 mb-4">
                    <Brain className="w-6 h-6 text-blue-600" />
                    <h3 className="font-semibold text-blue-900">AI-Powered Categorization</h3>
                  </div>
                  <ul className="text-sm text-blue-800 space-y-2">
                    <li>• **Semantic Analysis**: Content understanding and classification</li>
                    <li>• **Confidence Scoring**: AI certainty metrics (0.0-1.0)</li>
                    <li>• **Smart Suggestions**: Category and domain recommendations</li>
                    <li>• **Context Awareness**: Workspace-specific intelligence</li>
                  </ul>
                  <div className="mt-4 px-3 py-2 bg-blue-200 rounded text-xs text-blue-900">
                    <strong>AI Enhancement:</strong> Intelligent assistance, not replacement
                  </div>
                </div>

                <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg p-6 border border-orange-200">
                  <div className="flex items-center space-x-3 mb-4">
                    <Users className="w-6 h-6 text-orange-600" />
                    <h3 className="font-semibold text-orange-900">Bulk Operations</h3>
                  </div>
                  <ul className="text-sm text-orange-800 space-y-2">
                    <li>• **Multi-Select**: Select multiple insights for batch actions</li>
                    <li>• **Bulk Categorization**: Apply categories to multiple items</li>
                    <li>• **Mass Operations**: Delete, archive, or modify selections</li>
                    <li>• **Batch Export**: Export filtered insight collections</li>
                  </ul>
                  <div className="mt-4 px-3 py-2 bg-orange-200 rounded text-xs text-orange-900">
                    <strong>Efficiency:</strong> Manage large knowledge bases effectively
                  </div>
                </div>

                <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-6 border border-purple-200">
                  <div className="flex items-center space-x-3 mb-4">
                    <History className="w-6 h-6 text-purple-600" />
                    <h3 className="font-semibold text-purple-900">Audit Trail & Versioning</h3>
                  </div>
                  <ul className="text-sm text-purple-800 space-y-2">
                    <li>• **Complete History**: Track all changes with timestamps</li>
                    <li>• **User Attribution**: Know who made each modification</li>
                    <li>• **Version Control**: Maintain insight revision history</li>
                    <li>• **Undo System**: Reverse recent changes safely</li>
                  </ul>
                  <div className="mt-4 px-3 py-2 bg-purple-200 rounded text-xs text-purple-900">
                    <strong>Accountability:</strong> Full transparency and recoverability
                  </div>
                </div>
              </div>
            </section>

            {/* AI Categorization System */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                <Brain className="w-6 h-6 mr-3 text-indigo-600" />
                AI-Driven Categorization Engine
              </h2>

              <div className="bg-gradient-to-r from-indigo-50 to-indigo-100 rounded-lg p-6 border border-indigo-200 mb-6">
                <h3 className="font-semibold text-indigo-900 mb-4">Semantic Understanding</h3>
                <p className="text-indigo-800 text-sm mb-4">
                  The AI categorization engine analyzes content semantically to suggest appropriate categories 
                  and domain classifications, learning from workspace patterns and user preferences.
                </p>

                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-semibold text-indigo-900 mb-3">Analysis Process</h4>
                    <div className="space-y-2 text-sm text-indigo-800">
                      <div className="flex items-center space-x-2">
                        <div className="w-6 h-6 bg-indigo-200 rounded-full flex items-center justify-center text-xs font-bold text-indigo-900">1</div>
                        <span>Content semantic analysis and keyword extraction</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="w-6 h-6 bg-indigo-200 rounded-full flex items-center justify-center text-xs font-bold text-indigo-900">2</div>
                        <span>Workspace context integration and pattern matching</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="w-6 h-6 bg-indigo-200 rounded-full flex items-center justify-center text-xs font-bold text-indigo-900">3</div>
                        <span>Category confidence scoring and ranking</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="w-6 h-6 bg-indigo-200 rounded-full flex items-center justify-center text-xs font-bold text-indigo-900">4</div>
                        <span>User preference learning and refinement</span>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white rounded p-4 border border-indigo-300">
                    <h4 className="font-semibold text-indigo-900 mb-3">Example Classification</h4>
                    <div className="space-y-2 text-sm">
                      <div>
                        <strong className="text-indigo-900">Input:</strong>
                        <p className="text-gray-700">"Best practices for B2B email automation sequences"</p>
                      </div>
                      <div>
                        <strong className="text-indigo-900">AI Analysis:</strong>
                        <div className="mt-2 space-y-1">
                          <div className="flex justify-between">
                            <span className="text-gray-600">Category: Marketing</span>
                            <span className="text-green-600 font-semibold">92%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Domain: Business</span>
                            <span className="text-blue-600 font-semibold">88%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Subcategory: Email</span>
                            <span className="text-purple-600 font-semibold">95%</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="grid md:grid-cols-3 gap-6">
                <div className="bg-white rounded-lg p-6 border border-gray-200">
                  <h4 className="font-semibold text-gray-900 mb-3">Core Categories</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• **Marketing** - Campaigns, content, strategies</li>
                    <li>• **Technical** - Development, architecture, tools</li>
                    <li>• **Business** - Strategy, operations, planning</li>
                    <li>• **Process** - Workflows, procedures, standards</li>
                    <li>• **Research** - Market analysis, competitive intel</li>
                  </ul>
                </div>

                <div className="bg-white rounded-lg p-6 border border-gray-200">
                  <h4 className="font-semibold text-gray-900 mb-3">Domain Types</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• **Business** - Commercial and strategic insights</li>
                    <li>• **Technical** - Engineering and development</li>
                    <li>• **Creative** - Design and content creation</li>
                    <li>• **Operational** - Process and workflow</li>
                    <li>• **Research** - Data and analysis</li>
                  </ul>
                </div>

                <div className="bg-white rounded-lg p-6 border border-gray-200">
                  <h4 className="font-semibold text-gray-900 mb-3">Confidence Levels</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                      <span className="text-gray-600">90-100% - High confidence</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                      <span className="text-gray-600">70-89% - Good confidence</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                      <span className="text-gray-600">50-69% - Medium confidence</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                      <span className="text-gray-600">&lt; 50% - Manual review needed</span>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* User Interface & Experience */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                <Edit className="w-6 h-6 mr-3 text-indigo-600" />
                User Interface & Experience
              </h2>

              <div className="bg-gray-50 rounded-lg p-6 border border-gray-200 mb-6">
                <h3 className="font-semibold text-gray-900 mb-4">Knowledge Insights Manager Interface</h3>
                <p className="text-gray-600 text-sm mb-6">
                  The primary interface provides comprehensive insight management with intuitive controls 
                  and real-time AI assistance.
                </p>

                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-semibold text-gray-800 mb-3">Main Features</h4>
                    <ul className="text-sm text-gray-600 space-y-2">
                      <li className="flex items-center space-x-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        <span>**Rich Text Editor** - Formatted content creation</span>
                      </li>
                      <li className="flex items-center space-x-2">
                        <CheckCircle className="w-4 h-4 text-blue-600" />
                        <span>**Smart Search** - Semantic content discovery</span>
                      </li>
                      <li className="flex items-center space-x-2">
                        <CheckCircle className="w-4 h-4 text-purple-600" />
                        <span>**Category Filters** - Organized browsing</span>
                      </li>
                      <li className="flex items-center space-x-2">
                        <CheckCircle className="w-4 h-4 text-orange-600" />
                        <span>**Bulk Actions** - Multi-select operations</span>
                      </li>
                      <li className="flex items-center space-x-2">
                        <CheckCircle className="w-4 h-4 text-indigo-600" />
                        <span>**Live Suggestions** - Real-time AI categorization</span>
                      </li>
                    </ul>
                  </div>

                  <div>
                    <h4 className="font-semibold text-gray-800 mb-3">User Experience</h4>
                    <ul className="text-sm text-gray-600 space-y-2">
                      <li className="flex items-center space-x-2">
                        <Sparkles className="w-4 h-4 text-yellow-600" />
                        <span>**Instant Feedback** - Immediate AI suggestions</span>
                      </li>
                      <li className="flex items-center space-x-2">
                        <RotateCcw className="w-4 h-4 text-green-600" />
                        <span>**Undo Support** - Safe experimentation</span>
                      </li>
                      <li className="flex items-center space-x-2">
                        <History className="w-4 h-4 text-blue-600" />
                        <span>**Change History** - Complete audit trails</span>
                      </li>
                      <li className="flex items-center space-x-2">
                        <Search className="w-4 h-4 text-purple-600" />
                        <span>**Advanced Filters** - Precise content discovery</span>
                      </li>
                      <li className="flex items-center space-x-2">
                        <Database className="w-4 h-4 text-orange-600" />
                        <span>**Soft Delete** - Recovery-friendly deletion</span>
                      </li>
                    </ul>
                  </div>
                </div>
              </div>

              <div className="bg-yellow-50 rounded-lg p-6 border border-yellow-200">
                <div className="flex items-start space-x-3">
                  <AlertTriangle className="w-6 h-6 text-yellow-600 mt-1" />
                  <div>
                    <h3 className="text-lg font-semibold text-yellow-900">Human-Centric Design</h3>
                    <p className="text-yellow-700 mt-1">
                      Every feature prioritizes human control and understanding. AI provides assistance and suggestions, 
                      but all final decisions remain with the user. No automated actions occur without explicit consent.
                    </p>
                  </div>
                </div>
              </div>
            </section>

            {/* Technical Architecture */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                <Database className="w-6 h-6 mr-3 text-indigo-600" />
                Technical Architecture
              </h2>

              <div className="bg-gray-900 rounded-lg p-6 text-white mb-6">
                <h3 className="text-lg font-semibold mb-4 text-green-400">Backend Services</h3>
                <pre className="text-sm overflow-x-auto">
                  <code>{`# AI Knowledge Categorization Service
class AIKnowledgeCategorization:
    async def categorize_knowledge(
        self,
        content: str,
        title: str,
        workspace_context: Dict[str, Any]
    ) -> CategoryResult:
        """
        Analyze content semantically and suggest categories
        with confidence scoring and contextual awareness
        """
        
        # Semantic analysis
        analysis = await self.ai_analyzer.analyze_content(
            content, title, workspace_context
        )
        
        # Category matching and scoring
        categories = await self.match_categories(analysis)
        
        # Return with confidence scores
        return CategoryResult(
            primary_category=categories[0],
            confidence=analysis.confidence,
            suggestions=categories[1:5],
            reasoning=analysis.reasoning
        )

# User Insight Manager
class UserInsightManager:
    async def create_user_insight(
        self,
        workspace_id: str,
        title: str,
        content: str,
        category: str,
        domain_type: str,
        created_by: str,
        ai_suggestions: Optional[Dict] = None
    ) -> InsightResult:
        """
        Create insight with audit trail and validation
        """
        
        # Create insight with full metadata
        insight = await self.db.create_insight({
            "workspace_id": workspace_id,
            "title": title,
            "content": content,
            "category": category,
            "domain_type": domain_type,
            "created_by": created_by,
            "ai_metadata": ai_suggestions,
            "created_at": datetime.utcnow(),
            "version": 1
        })
        
        # Create audit trail entry
        await self.audit.log_action(
            workspace_id, created_by, "CREATE_INSIGHT", 
            insight.id, {"title": title}
        )
        
        return insight`}</code>
                </pre>
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
                  <h4 className="font-semibold text-blue-900 mb-3">Database Schema</h4>
                  <div className="bg-gray-900 rounded p-4 text-xs">
                    <pre className="text-green-400 overflow-x-auto">
                      <code>{`-- User insights table
CREATE TABLE user_insights (
  id UUID PRIMARY KEY,
  workspace_id UUID REFERENCES workspaces(id),
  title VARCHAR(255) NOT NULL,
  content TEXT NOT NULL,
  category VARCHAR(100),
  domain_type VARCHAR(100),
  created_by VARCHAR(255),
  ai_metadata JSONB,
  version INTEGER DEFAULT 1,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  deleted_at TIMESTAMP NULL
);

-- Audit trail table
CREATE TABLE insight_audit_log (
  id UUID PRIMARY KEY,
  insight_id UUID REFERENCES user_insights(id),
  workspace_id UUID,
  user_id VARCHAR(255),
  action VARCHAR(50),
  changes JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);`}</code>
                    </pre>
                  </div>
                </div>

                <div className="bg-green-50 rounded-lg p-6 border border-green-200">
                  <h4 className="font-semibold text-green-900 mb-3">API Endpoints</h4>
                  <ul className="text-sm text-green-800 space-y-1">
                    <li>• <code>GET /api/user-insights/{workspace_id}/insights</code></li>
                    <li>• <code>POST /api/user-insights/{workspace_id}/insights</code></li>
                    <li>• <code>PUT /api/user-insights/{workspace_id}/insights/{id}</code></li>
                    <li>• <code>DELETE /api/user-insights/{workspace_id}/insights/{id}</code></li>
                    <li>• <code>POST /api/user-insights/{workspace_id}/insights/bulk</code></li>
                    <li>• <code>GET /api/user-insights/categories/suggestions</code></li>
                    <li>• <code>GET /api/user-insights/{workspace_id}/audit</code></li>
                    <li>• <code>POST /api/user-insights/{workspace_id}/undo</code></li>
                  </ul>
                </div>
              </div>
            </section>

            {/* Advanced Features */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Advanced Features</h2>

              <div className="space-y-6">
                <div className="bg-gradient-to-r from-green-50 to-green-100 rounded-lg p-6 border border-green-200">
                  <h3 className="font-semibold text-green-900 mb-4 flex items-center">
                    <Search className="w-5 h-5 mr-2" />
                    Intelligent Search & Discovery
                  </h3>
                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-semibold text-green-800 mb-2">Search Capabilities</h4>
                      <ul className="text-sm text-green-700 space-y-1">
                        <li>• **Semantic Search** - Content meaning-based discovery</li>
                        <li>• **Keyword Matching** - Traditional text search</li>
                        <li>• **Category Filtering** - Organized browsing</li>
                        <li>• **Date Range Filtering** - Temporal organization</li>
                        <li>• **Author-based Filtering** - User-specific insights</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-semibold text-green-800 mb-2">Discovery Features</h4>
                      <ul className="text-sm text-green-700 space-y-1">
                        <li>• **Related Insights** - AI-suggested connections</li>
                        <li>• **Trending Topics** - Popular knowledge areas</li>
                        <li>• **Recent Activities** - Latest workspace insights</li>
                        <li>• **Recommended Reading** - Personalized suggestions</li>
                        <li>• **Knowledge Gaps** - Missing topic identification</li>
                      </ul>
                    </div>
                  </div>
                </div>

                <div className="bg-gradient-to-r from-purple-50 to-purple-100 rounded-lg p-6 border border-purple-200">
                  <h3 className="font-semibold text-purple-900 mb-4 flex items-center">
                    <History className="w-5 h-5 mr-2" />
                    Version Control & Recovery
                  </h3>
                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-semibold text-purple-800 mb-2">Version Management</h4>
                      <ul className="text-sm text-purple-700 space-y-1">
                        <li>• **Automatic Versioning** - Every edit creates new version</li>
                        <li>• **Change Diff Visualization** - See exactly what changed</li>
                        <li>• **Version Restoration** - Rollback to any previous state</li>
                        <li>• **Branch Comparison** - Compare different versions</li>
                        <li>• **Merge Capabilities** - Combine version changes</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-semibold text-purple-800 mb-2">Recovery Options</h4>
                      <ul className="text-sm text-purple-700 space-y-1">
                        <li>• **Soft Delete** - Deletion with recovery option</li>
                        <li>• **Trash Management** - Deleted items organization</li>
                        <li>• **Bulk Restoration** - Recover multiple items</li>
                        <li>• **Permanent Cleanup** - Final deletion control</li>
                        <li>• **Data Export** - Backup and archival</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Performance & Scalability */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Performance & Scalability</h2>

              <div className="grid md:grid-cols-4 gap-6 mb-6">
                <div className="bg-green-50 rounded-lg p-6 text-center border border-green-200">
                  <div className="text-3xl font-bold text-green-900 mb-2">< 200ms</div>
                  <div className="text-sm text-green-700">AI categorization response</div>
                </div>
                <div className="bg-blue-50 rounded-lg p-6 text-center border border-blue-200">
                  <div className="text-3xl font-bold text-blue-900 mb-2">10k+</div>
                  <div className="text-sm text-blue-700">Insights per workspace</div>
                </div>
                <div className="bg-purple-50 rounded-lg p-6 text-center border border-purple-200">
                  <div className="text-3xl font-bold text-purple-900 mb-2">100%</div>
                  <div className="text-sm text-purple-700">Audit trail coverage</div>
                </div>
                <div className="bg-orange-50 rounded-lg p-6 text-center border border-orange-200">
                  <div className="text-3xl font-bold text-orange-900 mb-2">99.9%</div>
                  <div className="text-sm text-orange-700">Data recovery success</div>
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-6">
                <h4 className="font-semibold text-gray-900 mb-4">Optimization Features</h4>
                <div className="grid md:grid-cols-2 gap-6 text-sm text-gray-600">
                  <div>
                    <h5 className="font-semibold text-gray-800 mb-2">Performance</h5>
                    <ul className="space-y-1">
                      <li>• **Intelligent Caching** - AI suggestion caching</li>
                      <li>• **Lazy Loading** - Progressive content loading</li>
                      <li>• **Database Indexing** - Optimized search queries</li>
                      <li>• **Content Compression** - Efficient storage</li>
                    </ul>
                  </div>
                  <div>
                    <h5 className="font-semibold text-gray-800 mb-2">Scalability</h5>
                    <ul className="space-y-1">
                      <li>• **Workspace Isolation** - Multi-tenant architecture</li>
                      <li>• **Horizontal Scaling** - Multiple service instances</li>
                      <li>• **Load Balancing** - Distributed request handling</li>
                      <li>• **Async Processing** - Non-blocking operations</li>
                    </ul>
                  </div>
                </div>
              </div>
            </section>

            {/* Configuration */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Configuration</h2>

              <div className="bg-gray-100 rounded-lg p-6">
                <h3 className="font-semibold text-gray-900 mb-4">Environment Variables</h3>
                <div className="space-y-3 text-sm">
                  <div className="flex flex-col space-y-1">
                    <code className="bg-gray-800 text-green-400 px-2 py-1 rounded">ENABLE_AI_CATEGORIZATION=true</code>
                    <span className="text-gray-600 text-xs">Enable AI-powered categorization</span>
                  </div>
                  <div className="flex flex-col space-y-1">
                    <code className="bg-gray-800 text-green-400 px-2 py-1 rounded">AI_CATEGORIZATION_CONFIDENCE_THRESHOLD=0.7</code>
                    <span className="text-gray-600 text-xs">Minimum confidence for auto-suggestions</span>
                  </div>
                  <div className="flex flex-col space-y-1">
                    <code className="bg-gray-800 text-green-400 px-2 py-1 rounded">MAX_INSIGHTS_PER_WORKSPACE=10000</code>
                    <span className="text-gray-600 text-xs">Maximum insights per workspace</span>
                  </div>
                  <div className="flex flex-col space-y-1">
                    <code className="bg-gray-800 text-green-400 px-2 py-1 rounded">INSIGHT_AUDIT_RETENTION_DAYS=365</code>
                    <span className="text-gray-600 text-xs">Audit trail retention period</span>
                  </div>
                  <div className="flex flex-col space-y-1">
                    <code className="bg-gray-800 text-green-400 px-2 py-1 rounded">ENABLE_SOFT_DELETE=true</code>
                    <span className="text-gray-600 text-xs">Enable recovery-friendly deletion</span>
                  </div>
                </div>
              </div>
            </section>

            {/* Related Concepts */}
            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Related Concepts</h2>
              
              <div className="grid md:grid-cols-3 gap-4">
                <Link 
                  href="/docs/core-concepts/memory"
                  className="block p-4 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors"
                >
                  <Brain className="w-5 h-5 text-blue-600 mb-2" />
                  <h3 className="font-semibold text-gray-900 mb-1">Memory</h3>
                  <p className="text-sm text-gray-600">Workspace memory and learning</p>
                </Link>

                <Link 
                  href="/docs/core-concepts/workspaces"
                  className="block p-4 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors"
                >
                  <Database className="w-5 h-5 text-green-600 mb-2" />
                  <h3 className="font-semibold text-gray-900 mb-1">Workspaces</h3>
                  <p className="text-sm text-gray-600">Multi-tenant workspace system</p>
                </Link>

                <Link 
                  href="/docs/ai-architecture/rag"
                  className="block p-4 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors"
                >
                  <Search className="w-5 h-5 text-purple-600 mb-2" />
                  <h3 className="font-semibold text-gray-900 mb-1">RAG System</h3>
                  <p className="text-sm text-gray-600">Document intelligence and search</p>
                </Link>
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  )
}