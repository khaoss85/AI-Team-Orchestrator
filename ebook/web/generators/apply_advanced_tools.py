#!/usr/bin/env python3

import os
import re
from pathlib import Path

# Advanced Reader Tools CSS (to be inserted before closing </style>)
READER_TOOLS_CSS = '''        /* Reader Tools */
        .reader-tools {
            position: fixed;
            top: 50%;
            right: 20px;
            transform: translateY(-50%);
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 1rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            z-index: 1000;
            display: flex;
            flex-direction: column;
            gap: 0.8rem;
            transition: all 0.3s ease;
            min-width: 60px;
        }
        
        .reader-tools.collapsed {
            width: 60px;
            padding: 0.8rem;
        }
        
        .reader-tool {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.6rem;
            border: none;
            background: transparent;
            cursor: pointer;
            border-radius: 8px;
            transition: all 0.2s ease;
            color: #495057;
            font-size: 0.85rem;
            white-space: nowrap;
        }
        
        .reader-tool:hover {
            background: rgba(102, 126, 234, 0.1);
            color: #667eea;
        }
        
        .reader-tool.active {
            background: #667eea;
            color: white;
        }
        
        .reader-tool-icon {
            font-size: 1.1rem;
            flex-shrink: 0;
        }
        
        .reader-tool-label {
            font-size: 0.8rem;
            font-weight: 500;
        }
        
        .collapsed .reader-tool-label {
            display: none;
        }
        
        .reader-tools-toggle {
            position: absolute;
            top: -10px;
            left: -10px;
            width: 30px;
            height: 30px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 50%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8rem;
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
        }
        
        /* Reading Progress */
        .reading-progress {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 3px;
            background: rgba(102, 126, 234, 0.2);
            z-index: 1001;
        }
        
        .reading-progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            width: 0%;
            transition: width 0.3s ease;
        }
        
        /* Dark Mode */
        body.dark-mode {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e9ecef;
        }
        
        .dark-mode .container {
            color: #e9ecef;
        }
        
        .dark-mode .chapter-header,
        .dark-mode .chapter-content {
            background: rgba(255, 255, 255, 0.05);
            color: #e9ecef;
        }
        
        .dark-mode .breadcrumb {
            background: rgba(255, 255, 255, 0.1);
            color: #e9ecef;
        }
        
        .dark-mode .reader-tools {
            background: rgba(0, 0, 0, 0.8);
            color: #e9ecef;
        }
        
        .dark-mode .reader-tool {
            color: #e9ecef;
        }
        
        .dark-mode .reader-tool:hover {
            background: rgba(255, 255, 255, 0.1);
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .reader-tools {
                right: 10px;
                padding: 0.8rem;
                min-width: 50px;
            }
            
            .reader-tools.collapsed {
                width: 50px;
                padding: 0.6rem;
            }
            
            .reader-tool {
                padding: 0.5rem;
            }
            
            .reader-tool-label {
                font-size: 0.75rem;
            }
        }

        /* Bookmark Toast */
        .bookmark-toast {
            position: fixed;
            top: 80px;
            right: 20px;
            background: #28a745;
            color: white;
            padding: 0.8rem 1.2rem;
            border-radius: 8px;
            z-index: 1002;
            transform: translateX(300px);
            transition: transform 0.3s ease;
            font-size: 0.9rem;
            box-shadow: 0 5px 15px rgba(40, 167, 69, 0.3);
        }
        
        .bookmark-toast.show {
            transform: translateX(0);
        }
        
        .bookmark-toast.error {
            background: #dc3545;
            box-shadow: 0 5px 15px rgba(220, 53, 69, 0.3);
        }

        /* Bookmarks Modal */
        .bookmarks-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 2000;
            backdrop-filter: blur(5px);
        }

        .bookmarks-modal.show {
            display: flex;
            align-items: center;
            justify-content: center;
            animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        .bookmarks-content {
            background: white;
            border-radius: 20px;
            padding: 2rem;
            max-width: 600px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            animation: slideUp 0.3s ease;
        }

        @keyframes slideUp {
            from { 
                transform: translateY(50px);
                opacity: 0;
            }
            to { 
                transform: translateY(0);
                opacity: 1;
            }
        }

        .dark-mode .bookmarks-content {
            background: #1a1a2e;
            color: #e9ecef;
        }

        .bookmarks-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid #667eea;
        }

        .bookmarks-title {
            font-size: 1.5rem;
            font-weight: 700;
            color: #2c3e50;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .dark-mode .bookmarks-title {
            color: #e9ecef;
        }

        .close-bookmarks {
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            color: #7f8c8d;
            width: 30px;
            height: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            transition: all 0.2s ease;
        }

        .close-bookmarks:hover {
            background: rgba(102, 126, 234, 0.1);
            color: #667eea;
        }

        .bookmarks-list {
            max-height: 400px;
            overflow-y: auto;
        }

        .bookmark-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 0.5rem;
            background: rgba(102, 126, 234, 0.05);
            transition: all 0.2s ease;
        }

        .bookmark-item:hover {
            background: rgba(102, 126, 234, 0.1);
            transform: translateX(5px);
        }

        .dark-mode .bookmark-item {
            background: rgba(255, 255, 255, 0.05);
        }

        .dark-mode .bookmark-item:hover {
            background: rgba(255, 255, 255, 0.1);
        }

        .bookmark-info {
            flex-grow: 1;
        }

        .bookmark-title {
            font-weight: 600;
            color: #2c3e50;
            text-decoration: none;
            font-size: 1rem;
            line-height: 1.4;
        }

        .dark-mode .bookmark-title {
            color: #e9ecef;
        }

        .bookmark-title:hover {
            color: #667eea;
        }

        .bookmark-date {
            font-size: 0.8rem;
            color: #7f8c8d;
            margin-top: 0.3rem;
        }

        .bookmark-actions {
            display: flex;
            gap: 0.5rem;
        }

        .bookmark-action {
            background: none;
            border: none;
            cursor: pointer;
            padding: 0.3rem;
            border-radius: 5px;
            transition: all 0.2s ease;
            color: #7f8c8d;
        }

        .bookmark-action:hover {
            background: rgba(220, 53, 69, 0.1);
            color: #dc3545;
        }

        .empty-bookmarks {
            text-align: center;
            padding: 2rem;
            color: #7f8c8d;
        }

        .empty-bookmarks-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
            opacity: 0.5;
        }

        /* Language Select */
        .language-select {
            background: transparent;
            border: none;
            color: inherit;
            font-size: 0.75rem;
            font-weight: 600;
            cursor: pointer;
            outline: none;
            min-width: 60px;
        }

        .language-select option {
            background: white;
            color: #2c3e50;
        }

        .dark-mode .language-select option {
            background: #1a1a2e;
            color: #e9ecef;
        }'''

# HTML for reader tools
READER_TOOLS_HTML = '''        <!-- Reader Tools -->
        <div class="reader-tools" id="readerTools">
            <button class="reader-tools-toggle" onclick="toggleReaderTools()">⚙</button>
            
            <div class="reader-tool" onclick="toggleTheme()">
                <span class="reader-tool-icon" id="themeIcon">🌙</span>
                <span class="reader-tool-label">Tema</span>
            </div>
            
            <div class="reader-tool" onclick="toggleBookmark()">
                <span class="reader-tool-icon">🔖</span>
                <span class="reader-tool-label">Bookmark</span>
            </div>
            
            <div class="reader-tool" onclick="showBookmarks()">
                <span class="reader-tool-icon">📚</span>
                <span class="reader-tool-label">My Bookmarks</span>
            </div>
            
            <div class="reader-tool">
                <span class="reader-tool-icon">🌐</span>
                <select class="language-select" onchange="switchLanguage(this.value)">
                    <option value="it" selected>Italiano</option>
                    <option value="en">English</option>
                </select>
            </div>
            
            <div class="reader-tool" onclick="showFontSizeMenu()">
                <span class="reader-tool-icon">🔤</span>
                <span class="reader-tool-label">Font</span>
            </div>
        </div>
        
        <!-- Reading Progress -->
        <div class="reading-progress">
            <div class="reading-progress-fill" id="progressFill"></div>
        </div>
        
        <!-- Bookmark Toast -->
        <div class="bookmark-toast" id="bookmarkToast">
            <span id="bookmarkMessage">Bookmark salvato!</span>
        </div>

        <!-- Bookmarks Modal -->
        <div class="bookmarks-modal" id="bookmarksModal" onclick="if(event.target === this) closeBookmarksModal()">
            <div class="bookmarks-content">
                <div class="bookmarks-header">
                    <h3 class="bookmarks-title">📚 I Miei Bookmark</h3>
                    <button class="close-bookmarks" onclick="closeBookmarksModal()">×</button>
                </div>
                <div class="bookmarks-list" id="bookmarksList">
                    <!-- Bookmarks will be loaded here -->
                </div>
            </div>
        </div>

'''

# JavaScript for reader tools
READER_TOOLS_JS = '''
    <script>

        // Reader Tools JavaScript
        let readerToolsCollapsed = false;
        
        // Initialize reader tools
        document.addEventListener('DOMContentLoaded', function() {
            initializeReaderTools();
            updateReadingProgress();
            loadUserPreferences();
        });
        
        // Toggle reader tools visibility
        function toggleReaderTools() {
            const tools = document.getElementById('readerTools');
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
            const pageTitle = document.querySelector('.chapter-title').textContent;
            
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
        }
        
        // Language switching
        function switchLanguage(lang) {
            const currentPath = window.location.pathname;
            let newPath;
            
            if (lang === 'en') {
                newPath = currentPath.replace('/it/', '/en/')
                    .replace('user-experience-trasparenza', 'user-experience-transparency')
                    .replace('esecuzione-qualita', 'execution-quality')
                    .replace('filosofia-core-architettura', 'core-philosophy-architecture');
            } else {
                newPath = currentPath.replace('/en/', '/it/')
                    .replace('user-experience-transparency', 'user-experience-trasparenza')
                    .replace('execution-quality', 'esecuzione-qualita')
                    .replace('core-philosophy-architecture', 'filosofia-core-architettura');
            }
            
            window.location.href = newPath;
        }

        // Show bookmarks modal
        function showBookmarks() {
            const bookmarks = JSON.parse(localStorage.getItem('bookmarks') || '[]');
            const modal = document.getElementById('bookmarksModal');
            const list = document.getElementById('bookmarksList');
            
            if (bookmarks.length === 0) {
                list.innerHTML = `
                    <div class="empty-bookmarks">
                        <div class="empty-bookmarks-icon">📚</div>
                        <p>Nessun bookmark salvato ancora.</p>
                        <p>Clicca sull'icona 🔖 per aggiungere questa pagina ai tuoi bookmark!</p>
                    </div>
                `;
            } else {
                list.innerHTML = bookmarks.map(bookmark => `
                    <div class="bookmark-item">
                        <div class="bookmark-info">
                            <a href="${bookmark.url}" class="bookmark-title">${bookmark.title}</a>
                            <div class="bookmark-date">Salvato il ${new Date(bookmark.timestamp).toLocaleDateString('it-IT')}</div>
                        </div>
                        <div class="bookmark-actions">
                            <button class="bookmark-action" onclick="deleteBookmark('${bookmark.url}')" title="Rimuovi bookmark">
                                🗑️
                            </button>
                        </div>
                    </div>
                `).join('');
            }
            
            modal.classList.add('show');
        }

        // Close bookmarks modal
        function closeBookmarksModal() {
            const modal = document.getElementById('bookmarksModal');
            modal.classList.remove('show');
        }

        // Delete bookmark
        function deleteBookmark(url) {
            let bookmarks = JSON.parse(localStorage.getItem('bookmarks') || '[]');
            bookmarks = bookmarks.filter(b => b.url !== url);
            localStorage.setItem('bookmarks', JSON.stringify(bookmarks));
            showBookmarks(); // Refresh the list
            showToast('Bookmark rimosso!', 'error');
        }
        
        // Font size menu (simplified)
        function showFontSizeMenu() {
            const currentSize = localStorage.getItem('fontSize') || 'medium';
            let newSize;
            
            switch (currentSize) {
                case 'small':
                    newSize = 'medium';
                    break;
                case 'medium':
                    newSize = 'large';
                    break;
                case 'large':
                    newSize = 'small';
                    break;
                default:
                    newSize = 'medium';
            }
            
            setFontSize(newSize);
            localStorage.setItem('fontSize', newSize);
            showToast(`Dimensione font: ${newSize}`, 'success');
        }
        
        // Set font size
        function setFontSize(size) {
            const root = document.documentElement;
            const sizes = {
                small: '0.9',
                medium: '1.0',
                large: '1.1'
            };
            root.style.fontSize = sizes[size] + 'em';
        }
        
        // Show toast notification
        function showToast(message, type = 'success') {
            const toast = document.getElementById('bookmarkToast');
            const messageEl = document.getElementById('bookmarkMessage');
            
            messageEl.textContent = message;
            toast.className = `bookmark-toast ${type === 'error' ? 'error' : ''} show`;
            
            setTimeout(() => {
                toast.classList.remove('show');
            }, 3000);
        }
        
        // Reading progress
        function updateReadingProgress() {
            const progressFill = document.getElementById('progressFill');
            
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
                document.getElementById('themeIcon').textContent = '☀️';
            }
            
            // Load font size
            const savedFontSize = localStorage.getItem('fontSize');
            if (savedFontSize) {
                setFontSize(savedFontSize);
            }
            
            // Load reader tools state
            const toolsCollapsed = localStorage.getItem('readerToolsCollapsed') === 'true';
            if (toolsCollapsed) {
                document.getElementById('readerTools').classList.add('collapsed');
                readerToolsCollapsed = true;
            }
        }
        
        // Initialize reader tools
        function initializeReaderTools() {
            // Check if current page is bookmarked
            const currentPage = window.location.pathname;
            const bookmarks = JSON.parse(localStorage.getItem('bookmarks') || '[]');
            const isBookmarked = bookmarks.some(b => b.url === currentPage);
            
            if (isBookmarked) {
                document.querySelector('.reader-tool:nth-child(3)').classList.add('active');
            }
        }
    </script>
'''

def apply_advanced_tools(html_file_path):
    """Apply advanced reader tools to an HTML file if not already present"""
    try:
        with open(html_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if already has advanced tools
        if 'showBookmarks' in content or 'bookmarks-modal' in content:
            print(f"SKIPPED: {html_file_path} (already has advanced tools)")
            return False
            
        # Add CSS before closing </style>
        style_pattern = r'(.*?)(\s*</style>)'
        content = re.sub(style_pattern, r'\1' + READER_TOOLS_CSS + r'\2', content, flags=re.DOTALL)
        
        # Add HTML tools before Mermaid.js
        mermaid_pattern = r'(\s*</div>\s*<!-- Mermaid\.js for diagrams -->)'
        content = re.sub(mermaid_pattern, READER_TOOLS_HTML + r'\1', content)
        
        # Add JavaScript before closing </body>
        body_pattern = r'(\s*</script>\s*\n*\s*</body>)'
        content = re.sub(body_pattern, READER_TOOLS_JS + r'\1', content)
        
        # Write back the modified content
        with open(html_file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"SUCCESS: Applied advanced tools to {html_file_path}")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to process {html_file_path}: {str(e)}")
        return False

def main():
    """Main function to apply advanced tools to all needed files"""
    base_dir = Path('.')
    
    # Files that need advanced tools
    files_to_process = []
    
    # Find all HTML files that don't have showBookmarks
    for html_file in base_dir.rglob('*/index.html'):
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            if 'showBookmarks' not in content and 'bookmarks-modal' not in content:
                files_to_process.append(html_file)
        except:
            continue
    
    print(f"Found {len(files_to_process)} files that need advanced reader tools")
    
    success_count = 0
    for file_path in files_to_process:
        if apply_advanced_tools(file_path):
            success_count += 1
    
    print(f"\nCOMPLETED: Successfully applied advanced tools to {success_count}/{len(files_to_process)} files")

if __name__ == "__main__":
    main()