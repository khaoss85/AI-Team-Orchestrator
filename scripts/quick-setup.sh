#!/bin/bash

# 🚀 AI Team Orchestrator - Quick Setup Script
# Automatically sets up the complete development environment in < 5 minutes

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Emojis for better UX
CHECK="✅"
ERROR="❌"
INFO="ℹ️"
ROCKET="🚀"
GEAR="⚙️"

print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                🤖 AI Team Orchestrator                      ║"
    echo "║            Quick Setup - Developer Environment              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "\n${BLUE}${GEAR} $1${NC}"
}

print_success() {
    echo -e "${GREEN}${CHECK} $1${NC}"
}

print_error() {
    echo -e "${RED}${ERROR} $1${NC}"
}

print_info() {
    echo -e "${YELLOW}${INFO} $1${NC}"
}

check_requirements() {
    print_step "Checking system requirements..."
    
    # Check Node.js
    if command -v node >/dev/null 2>&1; then
        NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
        if [ "$NODE_VERSION" -ge 18 ]; then
            print_success "Node.js $(node -v) ✓"
        else
            print_error "Node.js version 18+ required. Current: $(node -v)"
            exit 1
        fi
    else
        print_error "Node.js not found. Please install Node.js 18+ from https://nodejs.org/"
        exit 1
    fi
    
    # Check Python
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        if python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)' 2>/dev/null; then
            print_success "Python $PYTHON_VERSION ✓"
        else
            print_error "Python 3.11+ required. Current: $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python 3 not found. Please install Python 3.11+ from https://python.org/"
        exit 1
    fi
    
    # Check pip
    if command -v pip >/dev/null 2>&1 || command -v pip3 >/dev/null 2>&1; then
        print_success "pip ✓"
    else
        print_error "pip not found. Please install pip"
        exit 1
    fi
    
    # Check git
    if command -v git >/dev/null 2>&1; then
        print_success "Git $(git --version | cut -d' ' -f3) ✓"
    else
        print_error "Git not found. Please install Git from https://git-scm.com/"
        exit 1
    fi
}

setup_backend() {
    print_step "Setting up Python backend..."
    
    cd backend
    
    # Create virtual environment if not exists
    if [ ! -d "venv" ]; then
        print_info "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    print_info "Activating virtual environment..."
    source venv/bin/activate
    
    # Upgrade pip
    print_info "Upgrading pip..."
    pip install --upgrade pip > /dev/null 2>&1
    
    # Install dependencies
    print_info "Installing Python dependencies..."
    pip install -r requirements.txt > /dev/null 2>&1
    
    # Setup environment file
    if [ ! -f ".env" ]; then
        print_info "Setting up environment configuration..."
        cp .env.example .env
        print_info "📝 Please edit backend/.env with your API keys:"
        print_info "   - OPENAI_API_KEY (get from https://platform.openai.com/api-keys)"
        print_info "   - SUPABASE_URL (get from https://supabase.com/dashboard)"
        print_info "   - SUPABASE_KEY (get from https://supabase.com/dashboard)"
    fi
    
    print_success "Backend setup completed!"
    cd ..
}

setup_frontend() {
    print_step "Setting up Next.js frontend..."
    
    cd frontend
    
    # Install dependencies
    print_info "Installing Node.js dependencies..."
    npm install > /dev/null 2>&1
    
    print_success "Frontend setup completed!"
    cd ..
}

setup_git_hooks() {
    print_step "Setting up Git hooks for quality gates..."
    
    # Create pre-commit hook
    cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
echo "🛡️ Running quality gates before commit..."

# Run backend linting
cd backend
if command -v black >/dev/null 2>&1; then
    echo "📝 Formatting Python code..."
    black . --quiet || exit 1
fi

# Run frontend linting  
cd ../frontend
if [ -f "package.json" ]; then
    echo "📝 Linting TypeScript code..."
    npm run lint --silent || exit 1
fi

echo "✅ Quality gates passed! Proceeding with commit..."
EOF
    
    chmod +x .git/hooks/pre-commit
    print_success "Git hooks configured!"
}

create_dev_scripts() {
    print_step "Creating development scripts..."
    
    # Create start script
    cat > scripts/start-dev.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting AI Team Orchestrator development servers..."

# Start backend in background
cd backend
source venv/bin/activate
echo "📡 Starting FastAPI backend on http://localhost:8000"
python main.py &
BACKEND_PID=$!

# Start frontend in background  
cd ../frontend
echo "🖥️  Starting Next.js frontend on http://localhost:3000"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Development servers started!"
echo "📡 Backend:  http://localhost:8000"
echo "🖥️  Frontend: http://localhost:3000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for interrupt
trap "kill $BACKEND_PID $FRONTEND_PID" INT
wait
EOF
    
    # Create test script
    cat > scripts/run-tests.sh << 'EOF'
#!/bin/bash
echo "🧪 Running AI Team Orchestrator test suite..."

# Backend tests
echo "🐍 Running Python tests..."
cd backend
source venv/bin/activate
pytest --quiet || exit 1

# Frontend tests
echo "🌐 Running JavaScript tests..."
cd ../frontend
npm test -- --watchAll=false --silent || exit 1

echo "✅ All tests passed!"
EOF
    
    chmod +x scripts/start-dev.sh
    chmod +x scripts/run-tests.sh
    
    print_success "Development scripts created!"
}

run_health_check() {
    print_step "Running system health check..."
    
    # Check backend can import main modules
    cd backend
    source venv/bin/activate > /dev/null 2>&1
    if python3 -c "import fastapi, supabase, openai" 2>/dev/null; then
        print_success "Backend dependencies ✓"
    else
        print_error "Backend dependency issues detected"
        exit 1
    fi
    cd ..
    
    # Check frontend dependencies
    cd frontend
    if npm list --depth=0 > /dev/null 2>&1; then
        print_success "Frontend dependencies ✓"
    else
        print_error "Frontend dependency issues detected"
        exit 1
    fi
    cd ..
    
    print_success "Health check passed!"
}

print_final_instructions() {
    echo -e "\n${GREEN}╔══════════════════════════════════════════════════════════════╗"
    echo "║                    🎉 Setup Complete!                       ║"
    echo "╚══════════════════════════════════════════════════════════════╝${NC}"
    
    echo -e "\n${YELLOW}📝 Next Steps:${NC}"
    echo "1. Edit backend/.env with your API keys (OpenAI, Supabase)"
    echo "2. Run: ./scripts/start-dev.sh"
    echo "3. Visit: http://localhost:3000"
    
    echo -e "\n${YELLOW}🛠️ Development Commands:${NC}"
    echo "• ./scripts/start-dev.sh    - Start both servers"
    echo "• ./scripts/run-tests.sh    - Run test suite"
    echo "• ./scripts/run-quality-gates.sh - Run sub-agents"
    
    echo -e "\n${YELLOW}📚 Resources:${NC}"
    echo "• Documentation: README.md"
    echo "• Contributing: CONTRIBUTING.md"
    echo "• API Docs: http://localhost:8000/docs"
    
    echo -e "\n${BLUE}🤖 Features to Explore:${NC}"
    echo "• Real-time thinking processes"
    echo "• 8 specialized sub-agents"
    echo "• Cost-optimized quality gates"
    echo "• Autonomous recovery system"
    
    echo -e "\n${GREEN}Happy coding with AI Team Orchestrator! 🚀${NC}"
}

# Main execution
main() {
    print_header
    
    check_requirements
    setup_backend
    setup_frontend
    setup_git_hooks
    create_dev_scripts
    run_health_check
    
    print_final_instructions
}

# Run main function
main "$@"