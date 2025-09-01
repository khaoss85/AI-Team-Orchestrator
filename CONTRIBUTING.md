# 🤝 Contributing to AI Team Orchestrator

We're excited you're interested in contributing to AI Team Orchestrator! This guide will help you get started and ensure your contributions align with our project goals.

## 🌟 Ways to Contribute

### 🐛 **Bug Reports**
Found a bug? Help us improve by reporting it:
- Check [existing issues](https://github.com/khaoss85/multi-agents/issues) first
- Use our [bug report template](.github/ISSUE_TEMPLATE/bug_report.md)
- Include system details, error logs, and reproduction steps

### ✨ **Feature Requests**
Have an idea? We'd love to hear it:
- Check our [roadmap](README.md#roadmap) to see if it's already planned
- Open a [feature request issue](.github/ISSUE_TEMPLATE/feature_request.md)
- Explain the use case and expected behavior

### 🧪 **Sub-Agent Development**
Create specialized agents for the quality gates system:
- Follow our [Sub-Agent Guide](docs/SUB_AGENTS.md)
- Test with the [Agent Testing Framework](docs/AGENT_TESTING.md)
- Submit via pull request with documentation

### 📖 **Documentation**
Improve developer experience:
- Fix typos, clarify explanations
- Add examples and tutorials
- Translate documentation (we support multi-language)

## 🚀 Development Setup

### Prerequisites
- **Node.js 18+** and **Python 3.11+**
- **Git** with GPG signing enabled (recommended)
- **OpenAI API key** for testing AI features

### Local Environment
```bash
# 1. Fork the repository on GitHub
# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/multi-agents.git
cd ai-team-orchestrator

# 3. Add upstream remote
git remote add upstream https://github.com/khaoss85/multi-agents.git

# 4. Setup development environment
./scripts/dev-setup.sh
```

### Development Dependencies
```bash
# Backend development tools
cd backend
pip install -r requirements-dev.txt  # Includes: black, flake8, pytest, mypy

# Frontend development tools  
cd ../frontend
npm install --save-dev  # Includes: eslint, prettier, jest, testing-library
```

## 🛠️ Development Workflow

### 1. **Create Feature Branch**
```bash
git checkout main
git pull upstream main
git checkout -b feature/your-feature-name
```

### 2. **Development Process**
```bash
# Make your changes
# Run quality gates locally
./scripts/run-quality-gates.sh

# Test your changes
cd backend && pytest
cd ../frontend && npm test

# Format code
./scripts/format-code.sh
```

### 3. **Commit Guidelines**
Follow [Conventional Commits](https://www.conventionalcommits.org/):
```bash
# Format: type(scope): description
git commit -m "feat(sub-agents): add performance monitoring agent"
git commit -m "fix(thinking): resolve memory leak in process viewer"
git commit -m "docs(readme): improve quick start guide"
```

### 4. **Pull Request Process**
```bash
# Push to your fork
git push origin feature/your-feature-name

# Create PR on GitHub with:
# - Clear description of changes
# - Link to related issues
# - Screenshots/demos if UI changes
# - Updated documentation
```

## 🧪 Testing Guidelines

### **Backend Testing**
```bash
cd backend

# Unit tests
pytest tests/unit/

# Integration tests  
pytest tests/integration/

# Sub-agent tests
pytest tests/agents/

# Performance tests
pytest tests/performance/ --benchmark
```

### **Frontend Testing**
```bash
cd frontend

# Unit tests
npm test

# Component tests
npm run test:components

# E2E tests
npm run test:e2e

# Visual regression tests
npm run test:visual
```

### **Quality Gates Testing**
```bash
# Test all sub-agents locally
./scripts/test-sub-agents.sh

# Test specific agent
./scripts/test-agent.sh system-architect

# Performance benchmarking
./scripts/benchmark-agents.sh
```

## 🏗️ Architecture Guidelines

### **AI-First Development**
- **No Hard-Coding**: Use AI-driven logic instead of static rules
- **Domain Agnostic**: Code should work for any business sector
- **Explainable**: AI decisions should be transparent and debuggable

### **Sub-Agent Development**
```python
# Sub-agent template structure
from claude_agent import BaseAgent

class MySpecializedAgent(BaseAgent):
    model = "sonnet"  # or "opus"
    color = "blue"
    priority = "high"
    
    def analyze(self, context: dict) -> dict:
        """Analyze code changes and provide feedback"""
        pass
        
    def suggest_fixes(self, violations: list) -> list:
        """Suggest concrete fixes for violations"""
        pass
```

### **Code Style**
- **Backend**: Follow PEP 8, use type hints, async/await patterns
- **Frontend**: React hooks, TypeScript strict mode, functional components
- **Documentation**: Clear docstrings, inline comments for complex logic

### **Performance Requirements**
- **Sub-agents**: <3 seconds analysis time, <6k tokens per call
- **API Endpoints**: <500ms response time for common operations
- **Frontend**: <200ms time to interactive, lazy loading for heavy components

## 🛡️ Quality Gates

All contributions must pass our automated quality gates:

### **Director Review System**
Your PR will be automatically reviewed by our 8 sub-agents:
1. **🏗️ System Architect** - Architecture coherence
2. **🔧 SDK Guardian** - OpenAI SDK compliance  
3. **🗄️ DB Steward** - Database integrity
4. **📡 API Contract Guardian** - API consistency
5. **🛡️ Principles Guardian** - Security & best practices
6. **🎯 Placeholder Police** - Production readiness
7. **🧪 Test Sentinel** - Test quality
8. **📝 Docs Scribe** - Documentation sync

### **Manual Review Process**
After automated gates pass:
1. **Code Review** by maintainers
2. **Architecture Review** for significant changes
3. **Performance Review** for optimization PRs
4. **Security Review** for sensitive changes

## 🎯 Contribution Priorities

### **🔥 High Priority**
- **Cost Optimization**: Reduce AI API usage while maintaining quality
- **Performance**: Sub-agent efficiency improvements
- **Documentation**: Better developer onboarding
- **Testing**: Increase coverage and reliability

### **⭐ Medium Priority**  
- **New Sub-Agents**: Specialized quality gates
- **UI/UX**: Thinking process visualization improvements
- **Integration**: Support for more AI models
- **Automation**: Development workflow improvements

### **💡 Nice to Have**
- **Mobile**: React Native companion app
- **Analytics**: Advanced metrics and insights
- **Marketplace**: Sub-agent plugin ecosystem
- **Enterprise**: SSO and advanced security features

## 📚 Resources

### **Documentation**
- [Full Technical Guide](CLAUDE.md)
- [Architecture Deep-Dive](docs/ARCHITECTURE.md)
- [Sub-Agent Development](docs/SUB_AGENTS.md)
- [API Reference](docs/API_REFERENCE.md)

### **Community**
- [GitHub Discussions](https://github.com/khaoss85/multi-agents/discussions)
- [Issue Tracker](https://github.com/khaoss85/multi-agents/issues)
- [Discord Server](https://discord.gg/ai-team-orchestrator)

### **Learning Resources**
- [Multi-Agent Systems Concepts](docs/CONCEPTS.md)
- [AI-Driven Development Guide](docs/AI_DRIVEN_DEV.md)
- [Cost Optimization Strategies](docs/COST_OPTIMIZATION.md)

## 🏆 Recognition

Contributors are recognized in multiple ways:

### **Hall of Fame**
- **🥇 Top Contributors**: Featured in README
- **🎖️ Specialist Badges**: Expert in specific areas
- **📈 Impact Metrics**: Contributions tracked and celebrated

### **Swag & Rewards**
- **🎁 Contributor Swag**: T-shirts, stickers for significant contributions
- **🎫 Conference Tickets**: Speaking opportunities at AI events
- **💼 Job Referrals**: Connections to AI companies hiring

## 📄 Legal

By contributing to this project, you agree that:
- Your contributions will be licensed under the [MIT License](LICENSE)
- You have the right to submit your contributions
- Your contributions are your original work or properly attributed

---

## 🙏 Thank You

Thank you for contributing to AI Team Orchestrator! Your efforts help build the future of AI-driven development workflows.

**Questions?** Feel free to reach out via [GitHub Discussions](https://github.com/khaoss85/multi-agents/discussions) or open an issue.

*Let's build amazing AI systems together!* 🤖✨