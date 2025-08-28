/**
 * Shared Reader Tools JavaScript for Italian Ebook Pages
 * Centralized, clean, and error-free implementation
 */

// Global state
let readerToolsCollapsed = false;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeReaderTools();
    updateReadingProgress();
    loadUserPreferences();
    updateBookmarkButton();
});

// Toggle reader tools visibility
function toggleReaderTools() {
    const tools = document.getElementById('readerTools');
    if (!tools) return;
    
    readerToolsCollapsed = !readerToolsCollapsed;
    
    if (readerToolsCollapsed) {
        tools.classList.add('collapsed');
    } else {
        tools.classList.remove('collapsed');
    }
    
    localStorage.setItem('readerToolsCollapsed', readerToolsCollapsed);
}

// Theme toggle functionality
function toggleTheme() {
    const body = document.body;
    const themeIcon = document.getElementById('themeIcon');
    if (!themeIcon) return;
    
    const isDarkMode = body.classList.contains('dark-mode');
    
    if (isDarkMode) {
        body.classList.remove('dark-mode');
        themeIcon.textContent = '🌙';
        localStorage.setItem('theme', 'light');
    } else {
        body.classList.add('dark-mode');
        themeIcon.textContent = '☀️';
        localStorage.setItem('theme', 'dark');
    }
}

// Bookmark functionality
function toggleBookmark() {
    const currentPage = window.location.pathname;
    const pageTitle = document.querySelector('.chapter-title')?.textContent || 'Capitolo';
    
    let bookmarks = JSON.parse(localStorage.getItem('bookmarks') || '[]');
    const existingIndex = bookmarks.findIndex(b => b.url === currentPage);
    
    if (existingIndex > -1) {
        bookmarks.splice(existingIndex, 1);
        showToast('Bookmark rimosso!', 'error');
    } else {
        bookmarks.push({
            url: currentPage,
            title: pageTitle,
            timestamp: new Date().toISOString()
        });
        showToast('Bookmark salvato!', 'success');
    }
    
    localStorage.setItem('bookmarks', JSON.stringify(bookmarks));
    updateBookmarkButton();
}

// Show bookmarks modal
function showBookmarks() {
    createBookmarksModal();
    const modal = document.getElementById('bookmarksModal');
    const bookmarksList = document.getElementById('bookmarksList');
    if (!modal || !bookmarksList) return;
    
    const bookmarks = JSON.parse(localStorage.getItem('bookmarks') || '[]');
    
    if (bookmarks.length === 0) {
        bookmarksList.innerHTML = `
            <div class="no-bookmarks">
                <div class="no-bookmarks-icon">📚</div>
                <h3>Nessun bookmark salvato</h3>
                <p>Inizia a salvare i tuoi capitoli preferiti cliccando l'icona bookmark 🔖</p>
            </div>
        `;
    } else {
        bookmarksList.innerHTML = bookmarks.map(bookmark => `
            <div class="bookmark-item">
                <a href="${bookmark.url}" class="bookmark-link">
                    <div class="bookmark-title">${bookmark.title}</div>
                    <div class="bookmark-date">${new Date(bookmark.timestamp).toLocaleDateString('it-IT')}</div>
                </a>
                <button class="delete-bookmark" onclick="deleteBookmark('${bookmark.url}')">🗑️</button>
            </div>
        `).join('');
    }
    
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

// Close bookmarks modal
function closeBookmarksModal(event) {
    const modal = document.getElementById('bookmarksModal');
    if (modal && (!event || event.target === modal)) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }
}

// Delete bookmark
function deleteBookmark(url) {
    let bookmarks = JSON.parse(localStorage.getItem('bookmarks') || '[]');
    bookmarks = bookmarks.filter(b => b.url !== url);
    localStorage.setItem('bookmarks', JSON.stringify(bookmarks));
    showToast('Bookmark rimosso!', 'error');
    showBookmarks(); // Refresh the modal
}

// Font size functionality
function showFontSizeMenu() {
    const currentSize = localStorage.getItem('fontSize') || 'medium';
    const sizes = ['small', 'medium', 'large'];
    const currentIndex = sizes.indexOf(currentSize);
    const newSize = sizes[(currentIndex + 1) % sizes.length];
    
    setFontSize(newSize);
    localStorage.setItem('fontSize', newSize);
    
    const sizeLabels = {
        'small': 'piccolo',
        'medium': 'medio', 
        'large': 'grande'
    };
    showToast(`Dimensione font: ${sizeLabels[newSize]}`, 'success');
}

// Set font size
function setFontSize(size) {
    const body = document.body;
    body.classList.remove('font-small', 'font-medium', 'font-large');
    body.classList.add(`font-${size}`);
}

// Show toast notification
function showToast(message, type = 'success') {
    let toast = document.getElementById('bookmarkToast');
    
    // Create toast if it doesn't exist
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'bookmarkToast';
        toast.innerHTML = `<span id="bookmarkMessage"></span>`;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 24px;
            border-radius: 6px;
            color: white;
            font-weight: 500;
            z-index: 10001;
            transform: translateX(100%);
            transition: transform 0.3s ease;
            background: #28a745;
        `;
        document.body.appendChild(toast);
    }
    
    const messageEl = document.getElementById('bookmarkMessage');
    if (messageEl) messageEl.textContent = message;
    
    toast.style.background = type === 'error' ? '#dc3545' : '#28a745';
    toast.style.transform = 'translateX(0)';
    
    setTimeout(() => {
        toast.style.transform = 'translateX(100%)';
    }, 3000);
}

// Update bookmark button state
function updateBookmarkButton() {
    const currentPage = window.location.pathname;
    const bookmarks = JSON.parse(localStorage.getItem('bookmarks') || '[]');
    const isBookmarked = bookmarks.some(b => b.url === currentPage);
    
    const bookmarkTool = document.querySelector('.reader-tool[onclick*="toggleBookmark"]');
    if (bookmarkTool) {
        bookmarkTool.classList.toggle('active', isBookmarked);
    }
}

// Language switching
function switchLanguage(lang) {
    const currentPath = window.location.pathname;
    let newPath;
    
    // Complete URI mappings (IT -> EN)
    const uriMappings = {
        // Core Philosophy Architecture
        '/it/filosofia-core-architettura/i-15-pilastri-sistema-ai/': '/en/core-philosophy-architecture/15-pillars-ai-system/',
        '/it/filosofia-core-architettura/primo-agente-specialist-architecture/': '/en/core-philosophy-architecture/first-specialist-agent-architecture/',
        '/it/filosofia-core-architettura/isolare-intelligenza-mock-llm/': '/en/core-philosophy-architecture/ai-mocking-testing-strategy/',
        '/it/filosofia-core-architettura/orchestratore-direttore-orchestra/': '/en/core-philosophy-architecture/orchestrator-conductor/',
        '/it/filosofia-core-architettura/recruiter-ai-team-dinamico/': '/en/core-philosophy-architecture/ai-recruiter-dynamic-team/',
        '/it/filosofia-core-architettura/dramma-parsing-contratto-ai/': '/en/core-philosophy-architecture/drama-parsing-ai-contracts/',
        '/it/filosofia-core-architettura/parsing-contratti-ai-affidabili/': '/en/core-philosophy-architecture/drama-parsing-ai-contracts/',
        '/it/filosofia-core-architettura/staffetta-mancata-handoff/': '/en/core-philosophy-architecture/failed-handoff-delegation/',
        '/it/filosofia-core-architettura/test-tool-ancorare-realta/': '/en/core-philosophy-architecture/tool-testing-reality-anchor/',
        '/it/filosofia-core-architettura/cassetta-attrezzi-agente/': '/en/core-philosophy-architecture/agent-toolbox/',
        '/it/filosofia-core-architettura/agente-ambiente-interazioni-fondamentali/': '/en/core-philosophy-architecture/agent-environment-interactions/',
        '/it/filosofia-core-architettura/agente-ambiente-database-shared/': '/en/core-philosophy-architecture/agent-environment-interactions/',
        '/it/filosofia-core-architettura/sdk-vs-api-battle/': '/en/core-philosophy-architecture/sdk-vs-api-battle/',
        
        // Execution Quality
        '/it/esecuzione-qualita/test-comprensivo-esame-maturita/': '/en/execution-quality/comprehensive-test/',
        '/it/esecuzione-qualita/assemblaggio-finale-ultimo-miglio/': '/en/execution-quality/final-assembly-last-mile/',
        '/it/esecuzione-qualita/test-produzione-sopravvivere/': '/en/execution-quality/production-test/',
        '/it/esecuzione-qualita/monitoraggio-autonomo-controllo/': '/en/execution-quality/autonomous-monitoring/',
        '/it/esecuzione-qualita/quality-gate-human-loop/': '/en/execution-quality/quality-gates-human-loop/',
        '/it/esecuzione-qualita/test-consolidamento-semplificare/': '/en/execution-quality/consolidation-test/',
        '/it/esecuzione-qualita/sistema-memoria-agente-impara/': '/en/execution-quality/memory-system-learning/',
        '/it/esecuzione-qualita/ciclo-miglioramento-auto-correzione/': '/en/execution-quality/improvement-cycle-correction/',
        
        // User Experience Transparency
        '/it/user-experience-trasparenza/chat-contestuale-dialogare-team-ai/': '/en/user-experience-transparency/contextual-chat/',
        '/it/user-experience-trasparenza/prossima-frontiera-agente-stratega/': '/en/user-experience-transparency/strategist-agent/',
        '/it/user-experience-trasparenza/onboarding-ux-esperienza-utente/': '/en/user-experience-transparency/onboarding-ux/',
        '/it/user-experience-trasparenza/organigramma-team-ai-chi-fa-cosa/': '/en/user-experience-transparency/ai-team-org-chart/',
        '/it/user-experience-trasparenza/conclusione-team-non-tool/': '/en/user-experience-transparency/team-not-tool/',
        '/it/user-experience-trasparenza/sintesi-astrazione-funzionale/': '/en/user-experience-transparency/synthesis-abstraction/',
        '/it/user-experience-trasparenza/antitesi-fitness-sfidare-limiti/': '/en/user-experience-transparency/fitness-antithesis/',
        '/it/user-experience-trasparenza/tesi-b2b-saas-versatilita/': '/en/user-experience-transparency/b2b-saas-thesis/',
        '/it/user-experience-trasparenza/bivio-architetturale-qa-chain/': '/en/user-experience-transparency/qa-chain-of-thought/',
        '/it/user-experience-trasparenza/deep-reasoning-scatola-nera/': '/en/user-experience-transparency/deep-reasoning/',
        '/it/user-experience-trasparenza/sala-controllo-monitoring-telemetria/': '/en/user-experience-transparency/control-room/',
        '/it/user-experience-trasparenza/stack-tecnologico-fondamenta/': '/en/user-experience-transparency/tech-stack/',
        
        // Memory System Scaling
        '/it/memory-system-scaling/load-testing-shock-successo-nemico/': '/en/memory-system-scaling/load-testing-shock/',
        '/it/memory-system-scaling/sistema-caching-semantico-ottimizzazione/': '/en/memory-system-scaling/semantic-caching/',
        '/it/memory-system-scaling/service-registry-architecture-ecosistema/': '/en/memory-system-scaling/service-registry/',
        '/it/memory-system-scaling/holistic-memory-consolidation-unificazione/': '/en/memory-system-scaling/memory-consolidation/',
        '/it/memory-system-scaling/global-scale-architecture-timezone/': '/en/memory-system-scaling/global-scale/',
        '/it/memory-system-scaling/grande-refactoring-universal-pipeline/': '/en/memory-system-scaling/great-refactoring/',
        '/it/memory-system-scaling/production-readiness-audit-moment-truth/': '/en/memory-system-scaling/production-readiness-audit/',
        '/it/memory-system-scaling/epilogo-mvp-global-platform-viaggio/': '/en/memory-system-scaling/epilogue-journey/',
        '/it/memory-system-scaling/guerra-orchestratori-unified/': '/en/memory-system-scaling/orchestrator-wars/',
        '/it/memory-system-scaling/enterprise-security-hardening-paranoia/': '/en/memory-system-scaling/security-hardening/',
        '/it/memory-system-scaling/rate-limiting-circuit-breakers-resilienza/': '/en/memory-system-scaling/rate-limiting-resilience/'
    };
    
    if (lang === 'en') {
        // Direct URI mapping for IT -> EN
        newPath = uriMappings[currentPath];
    } else if (lang === 'it') {
        // Reverse mapping for EN -> IT
        const reverseMapping = {};
        Object.keys(uriMappings).forEach(it => {
            reverseMapping[uriMappings[it]] = it;
        });
        newPath = reverseMapping[currentPath];
    }
    
    if (newPath && newPath !== currentPath) {
        window.location.href = newPath;
    }
}

// Reading progress functionality
function updateReadingProgress() {
    const progressFill = document.getElementById('progressFill');
    if (!progressFill) return;
    
    window.addEventListener('scroll', () => {
        const article = document.querySelector('.chapter-content');
        if (!article) return;
        
        const articleTop = article.offsetTop;
        const articleHeight = article.offsetHeight;
        const windowHeight = window.innerHeight;
        const scrollTop = window.pageYOffset;
        
        const progress = Math.min(100, Math.max(0, 
            ((scrollTop + windowHeight - articleTop) / articleHeight) * 100
        ));
        
        progressFill.style.width = progress + '%';
    });
}

// Load user preferences
function loadUserPreferences() {
    // Load theme
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
        const themeIcon = document.getElementById('themeIcon');
        if (themeIcon) themeIcon.textContent = '☀️';
    }
    
    // Load font size
    const savedFontSize = localStorage.getItem('fontSize');
    if (savedFontSize) {
        setFontSize(savedFontSize);
    }
    
    // Load reader tools state
    const toolsCollapsed = localStorage.getItem('readerToolsCollapsed') === 'true';
    if (toolsCollapsed) {
        const tools = document.getElementById('readerTools');
        if (tools) {
            tools.classList.add('collapsed');
            readerToolsCollapsed = true;
        }
    }
}

// Initialize reader tools
function initializeReaderTools() {
    updateBookmarkButton();
}

// Create bookmarks modal dynamically
function createBookmarksModal() {
    if (document.getElementById('bookmarksModal')) return;
    
    const modal = document.createElement('div');
    modal.id = 'bookmarksModal';
    modal.innerHTML = `
        <div class="bookmarks-content">
            <div class="bookmarks-header">
                <h3>I Miei Bookmark</h3>
                <button onclick="closeBookmarksModal()" class="close-bookmarks">&times;</button>
            </div>
            <div id="bookmarksList" class="bookmarks-list"></div>
        </div>
    `;
    modal.onclick = closeBookmarksModal;
    document.body.appendChild(modal);
}