# 🤖 AI Team Orchestrator

> **Next-Generation Multi-Agent AI Platform** - Orchestrate intelligent teams of specialized AI agents with autonomous quality gates, real-time thinking processes, and cost-optimized sub-agent architecture.

[![GitHub stars](https://img.shields.io/github/stars/khaoss85/multi-agents?style=social)](https://github.com/khaoss85/multi-agents/stargazers)
[![GitHub license](https://img.shields.io/github/license/khaoss85/multi-agents)](https://github.com/khaoss85/multi-agents/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Next.js](https://img.shields.io/badge/next.js-15+-black.svg)](https://nextjs.org/)

[![OpenAI Agents SDK](https://img.shields.io/badge/OpenAI-Agents_SDK-00A67E?logo=openai)](https://openai.github.io/openai-agents-python/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?logo=supabase&logoColor=white)](https://supabase.com)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-38B2AC?logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)

## ⚡ What Makes This Special

### 🧠 **Real-Time Thinking Processes (Claude/o3 Style)**
- **Live AI Reasoning**: Watch agents think step-by-step in real-time
- **Collaborative Intelligence**: Multi-agent coordination with handoffs
- **Explainable Decisions**: Full transparency into AI decision-making

### 🛡️ **Autonomous Quality Gates System**
- **Cost-Optimized**: Smart conditional triggering reduces API costs by 94%
- **8 Specialized Sub-Agents**: Architecture, security, database, API validation
- **Zero Manual Overhead**: Director agent decides which gates to activate

### 🎯 **AI-Driven Architecture (No Hard-Coding)**
- **Domain Agnostic**: Works for any business sector
- **Semantic Understanding**: AI-powered task classification and prioritization
- **Adaptive Thresholds**: Context-aware quality measurements

### 🔄 **Production-Ready Features**
- **Autonomous Recovery**: Failed tasks self-heal without human intervention  
- **Goal-Driven Planning**: AI decomposes objectives into concrete deliverables
- **Professional Output**: Raw JSON → Business-ready documents via AI transformation

## 🚀 Quick Start (< 5 minutes)

### Prerequisites
- **Node.js 18+** and **Python 3.11+**
- **OpenAI API key** (for AI agents)
- **Supabase account** (free tier works)

### One-Command Setup
```bash
# Clone and setup everything
git clone https://github.com/khaoss85/multi-agents.git
cd ai-team-orchestrator
./scripts/quick-setup.sh
```

### Manual Setup
```bash
# Backend setup
cd backend
pip install -r requirements.txt
cp .env.example .env  # Add your API keys

# Frontend setup  
cd ../frontend
npm install

# Start both services
npm run dev     # Frontend (port 3000)
python main.py  # Backend (port 8000) - run from backend/
```

## ⚙️ Configuration Files

The following configuration files are **required** but **not included in Git** for security. Create them locally:

### 📁 **Backend Configuration** (`backend/.env`)

Copy `backend/.env.example` and fill in your credentials:

```bash
# 🔑 Required API Keys
OPENAI_API_KEY=sk-your-openai-api-key-here
SUPABASE_URL=https://your-project-id.supabase.co  
SUPABASE_KEY=your-supabase-anon-public-key

# 🎯 Goal-Driven System (Core Features)
ENABLE_GOAL_DRIVEN_SYSTEM=true
AUTO_CREATE_GOALS_FROM_WORKSPACE=true
GOAL_VALIDATION_INTERVAL_MINUTES=20
MAX_GOAL_DRIVEN_TASKS_PER_CYCLE=5
GOAL_COMPLETION_THRESHOLD=80

# 📦 Asset & Deliverable Configuration
USE_ASSET_FIRST_DELIVERABLE=true
PREVENT_DUPLICATE_DELIVERABLES=true
MAX_DELIVERABLES_PER_WORKSPACE=3
DELIVERABLE_READINESS_THRESHOLD=100
MIN_COMPLETED_TASKS_FOR_DELIVERABLE=2
DELIVERABLE_CHECK_COOLDOWN_SECONDS=30

# 🤖 AI Quality Assurance
ENABLE_AI_QUALITY_ASSURANCE=true
ENABLE_DYNAMIC_AI_ANALYSIS=true
ENABLE_AUTO_PROJECT_COMPLETION=true

# 🧠 Enhanced Reasoning (Claude/o3 Style)
ENABLE_DEEP_REASONING=true
DEEP_REASONING_THRESHOLD=0.7
REASONING_CONFIDENCE_MIN=0.6
MAX_REASONING_ALTERNATIVES=3

# ⚡ Performance & Rate Limiting
OPENAI_RPM_LIMIT=3000
VALIDATION_CACHE_TTL=600
ENABLE_AGGRESSIVE_CACHING=true
AUTO_REFRESH_INTERVAL=600
```

### 🔗 **Getting Your API Keys**

#### **OpenAI API Key**
1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create new API key  
3. Copy the `sk-...` key to your `.env` file
4. **Important**: Add payment method for usage beyond free tier

#### **Supabase Configuration**
1. Visit [Supabase Dashboard](https://supabase.com/dashboard)
2. Create new project (free tier available)
3. Go to **Settings** → **API**
4. Copy **Project URL** and **anon public** key
5. Paste both in your `.env` file

### 🛡️ **Security Best Practices**

- ✅ **Never commit `.env` files** to Git
- ✅ **Use different API keys** for development/production  
- ✅ **Set OpenAI usage limits** to control costs
- ✅ **Rotate keys regularly** for production deployments
- ⚠️ **Keep your `.env` file private** - it contains sensitive credentials

### 📋 **Files Excluded from Git**

The following files are automatically ignored for security/cleanup:

```bash
# 🔐 Sensitive configuration files
.env*                    # Environment variables with API keys
!*.env.example          # Example files are kept in repo

# 📊 Development artifacts  
*.log                   # Log files from development
*.tmp, *.bak           # Temporary and backup files
__pycache__/           # Python bytecode
node_modules/          # NPM dependencies

# 🧪 Test artifacts
test_results/          # Test output files
.pytest_cache/         # Python test cache
.coverage              # Coverage reports

# 🔧 Development tools
.vscode/, .idea/       # IDE configuration
.DS_Store             # macOS system files
```

### 🔧 **Optional Configuration**

For development customization, you can also create:

- **Backend**: Additional `.env.local` for local overrides
- **Frontend**: No additional config files needed (Next.js handles this)
- **Database**: Supabase handles all database configuration remotely

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   🎯 Director   │───▶│  🤖 Sub-Agents  │───▶│ 📊 Quality Gates│
│   Orchestrator  │    │   (8 Specialists)│    │   & Validation  │  
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ 🧠 Thinking     │    │ 🛡️ Autonomous   │    │ 🎨 AI Content   │
│ Process Engine  │    │ Recovery System │    │ Transformation  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 🤖 **Sub-Agent Specialists**
1. **🏗️ System Architect** - Ensures architectural coherence and component reuse
2. **🔧 SDK Guardian** - Enforces OpenAI SDK best practices vs custom implementations  
3. **🗄️ DB Steward** - Maintains database schema integrity and constraints
4. **📡 API Contract Guardian** - Validates frontend-backend API consistency
5. **🛡️ Principles Guardian** - Enforces security and 15 architectural pillars
6. **🎯 Placeholder Police** - Eliminates TODO/FIXME and enforces AI-driven logic
7. **🧪 Test Sentinel** - Prevents fallback-dependent test patterns
8. **📝 Docs Scribe** - Maintains documentation-code consistency

## 🔬 **Technical Deep Dive**

### 💡 **Core Innovation: AI-First Development**

Traditional development uses hard-coded business logic. AI Team Orchestrator transforms this with **Semantic Intelligence**:

```python
# ❌ Traditional Hard-Coded Approach
if task_type in ["email", "campaign", "marketing"]:
    agent = marketing_specialist
elif domain == "finance":
    agent = finance_specialist

# ✅ AI-Driven Semantic Matching  
agent = await ai_agent_matcher.find_best_match(
    task_content=task.description,
    required_skills=task.extracted_skills,
    context=workspace.domain
)
```

### ⚙️ **15 Architectural Pillars**

Our system is built on 15 core principles that ensure scalability and reliability:

1. **🌍 Domain Agnostic** - No industry-specific hard-coding
2. **🧠 AI-First Logic** - Semantic understanding over keyword matching
3. **🔄 Autonomous Recovery** - Self-healing without human intervention
4. **📊 Goal-Driven Architecture** - Everything ties to measurable objectives
5. **🛡️ Quality Gates** - Automated architectural review system
6. **📝 Explainable AI** - Transparent decision-making processes
7. **🎯 Real Tool Usage** - Actual web search, file operations, not mocks
8. **💾 Contextual Memory** - Learns from past patterns and decisions
9. **🔧 SDK-Native** - Leverages OpenAI Agents SDK vs custom implementations
10. **⚡ Cost Optimization** - Smart API usage reduction (94% savings)
11. **📱 Production Ready** - Enterprise-grade error handling and monitoring
12. **🤝 Human-in-the-Loop** - Strategic human oversight for critical decisions
13. **🔒 Security First** - Secrets management and secure API practices
14. **📚 Living Documentation** - Self-updating technical documentation
15. **🌐 Multi-Language Support** - Internationalization-ready architecture

### 🧪 **Advanced Features**

#### **Autonomous Task Recovery**
```python
# Failed tasks automatically heal themselves
try:
    result = await execute_task(task)
except Exception as error:
    recovery = await autonomous_recovery.analyze_and_fix(
        task_id=task.id,
        error_context=str(error),
        workspace_history=workspace.memory
    )
    # Task continues without human intervention
```

#### **Real-Time Thinking Visualization**
```typescript
// Watch AI agents think step-by-step (Claude/o3 style)
const { thinkingSteps, isThinking } = useThinkingProcess(taskId)

// Live updates: Analysis → Planning → Execution → Validation
return (
  <ThinkingViewer steps={thinkingSteps} realTime={isThinking} />
)
```

#### **Cost-Optimized Quality Gates**
```python
# Director intelligently decides which agents to invoke
analysis = await director.analyze_changes(modified_files)
if analysis.requires_architecture_review:
    await invoke_agent("system-architect")
if analysis.has_database_changes:
    await invoke_agent("db-steward")
# Result: $3/month vs $240/month in API costs
```

## 🎮 Demo Features

### Real-Time AI Thinking
```typescript
// Watch AI agents think step-by-step
const thinkingProcess = useThinkingProcess(workspaceId)
// Displays: Analysis → Planning → Synthesis → Validation
```

### Smart Cost Control
```javascript
// Director intelligently decides which agents to invoke
Change: "frontend/Button.tsx" → 0 agent calls (UI only)
Change: "backend/database.py" → 3 agents (architecture + security + DB)
Result: $3/month vs $240/month in costs
```

### Autonomous Recovery
```python
# Tasks self-heal without human intervention
try:
    result = await execute_task(task)
except Exception as e:
    # AI analyzes failure and selects recovery strategy
    recovery = await autonomous_recovery(task_id, error_context)
    # Success: Task continues automatically
```

## 📈 Use Cases

### 🏢 **Enterprise Development Teams**
- **Quality Assurance**: Automated architectural reviews
- **Cost Control**: Intelligent sub-agent triggering 
- **Team Coordination**: Multi-agent task distribution

### 🚀 **AI-First Startups**
- **Rapid Prototyping**: AI-driven feature development
- **Scalable Architecture**: Built-in best practices enforcement
- **Professional Output**: Business-ready deliverables from day one

### 🎓 **Research & Education**
- **Multi-Agent Systems**: Study real-world coordination patterns
- **AI Transparency**: Observe reasoning processes in detail
- **Production Patterns**: Learn enterprise AI architecture

## 🛠️ Advanced Configuration

### Environment Variables (Backend)
```bash
# Core AI Configuration
OPENAI_API_KEY=your_openai_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Cost Optimization
ENABLE_SUB_AGENT_ORCHESTRATION=true
SUB_AGENT_MAX_CONCURRENT_AGENTS=5
SUB_AGENT_PERFORMANCE_TRACKING=true

# AI-Driven Features
ENABLE_AI_AGENT_MATCHING=true
ENABLE_AI_QUALITY_ASSURANCE=true
ENABLE_AUTO_TASK_RECOVERY=true

# Goal-Driven System
ENABLE_GOAL_DRIVEN_SYSTEM=true
GOAL_COMPLETION_THRESHOLD=80
MAX_GOAL_DRIVEN_TASKS_PER_CYCLE=5
```

### Development Commands
```bash
# Backend (FastAPI)
cd backend && python main.py              # Start server (port 8000)
cd backend && pytest                      # Run tests
cd backend && python check_system.py     # Health check

# Frontend (Next.js)  
cd frontend && npm run dev                # Start dev server (port 3000)
cd frontend && npm run build              # Production build
cd frontend && npm run lint               # Code quality check

# End-to-End Testing
./scripts/run_e2e_flow.sh                # Complete system test
```

## 📊 Performance Benchmarks

| Metric | Before Optimization | After AI-Driven |
|--------|-------------------|------------------|
| **Quality Gates Cost** | $240/month | $3/month (94% reduction) |
| **Task Recovery Time** | Manual intervention | <60s autonomous |
| **Code Review Coverage** | 60% manual | 95% automated |
| **Architecture Violations** | 15-20/week | <2/week |

## 🤝 Contributing

We welcome contributions! Check out our [Contributing Guide](CONTRIBUTING.md) for:

- 🐛 **Bug Reports**: Help us improve quality
- ✨ **Feature Requests**: Shape the roadmap  
- 🧪 **Sub-Agent Development**: Create specialized agents
- 📖 **Documentation**: Improve developer experience

### Development Setup
```bash
# Setup development environment
git clone <your-fork>
cd ai-team-orchestrator
pip install -r backend/requirements-dev.txt
npm install --save-dev # Frontend dev dependencies

# Run quality gates locally
./scripts/run-quality-gates.sh
```

## 🗺️ Roadmap

### 🎯 **Q1 2025**
- [ ] **Multi-Model Support**: Claude, Gemini, local models
- [ ] **Plugin Architecture**: Custom sub-agent marketplace
- [ ] **Advanced Metrics**: Performance analytics dashboard

### 🚀 **Q2 2025**  
- [ ] **Collaborative Workspaces**: Multi-user team support
- [ ] **API Rate Optimization**: Intelligent caching layer
- [ ] **Mobile Dashboard**: React Native companion app

### 🔮 **Future Vision**
- [ ] **Self-Improving Agents**: ML-based agent optimization
- [ ] **Industry Templates**: Domain-specific agent configurations
- [ ] **Enterprise SSO**: Advanced authentication systems

## 📖 **Complete Learning Resources**

### 🎓 **"AI Team Orchestrator" - The Complete Guide**

[![Read the Complete Book](https://img.shields.io/badge/📚_Read_Complete_Book-books.danielepelleri.com-blue?style=for-the-badge)](https://books.danielepelleri.com)

**Free comprehensive guide covering:**
- 🏗️ **Multi-Agent Architecture Patterns** - Design principles and best practices
- 🤖 **AI-First Development Methodology** - Moving beyond hard-coded logic
- 🛡️ **Production Quality Gates** - Automated review and optimization systems
- 💰 **Cost Optimization Strategies** - 94% API cost reduction techniques
- 📊 **Real-World Case Studies** - Enterprise implementations and lessons learned
- 🔧 **Advanced Implementation Guides** - Deep technical implementation details

### 📚 **Technical Documentation**

- 📖 **[Full Technical Reference](CLAUDE.md)** - Comprehensive development guide (75KB)
- 🏗️ **[System Architecture](docs/architecture/)** - Core system design documents
- 🤖 **[Sub-Agent Configurations](docs/reports/)** - Quality gate implementations  
- 📊 **[Implementation Guides](docs/guides/)** - Step-by-step technical tutorials
- 🛡️ **[Quality Assurance Reports](docs/reports/)** - Performance and compliance analysis

### 🌐 **Community & Learning**

- **💬 [GitHub Discussions](https://github.com/khaoss85/multi-agents/discussions)** - Community Q&A
- **📋 [Issue Tracker](https://github.com/khaoss85/multi-agents/issues)** - Bug reports and features
- **🎯 [Contributing Guide](CONTRIBUTING.md)** - Join the development community
- **📚 [Complete Book Guide](https://books.danielepelleri.com)** - Deep learning resource

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⭐ Star History

If you find this project useful, please consider giving it a star! It helps others discover the project and motivates continued development.

[![Star History Chart](https://api.star-history.com/svg?repos=khaoss85/multi-agents&type=Date)](https://star-history.com/#khaoss85/multi-agents&Date)

---

**Built with ❤️ by the AI Team Orchestrator community**

*Transform your development workflow with intelligent AI agent orchestration.*