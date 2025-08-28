#!/usr/bin/env python3

import os
import re
import glob

# Reader tools component HTML/CSS/JS
READER_TOOLS = """
        /* Reader Tools */
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
        
        /* Language Switcher */
        .language-switcher {
            display: flex;
            background: rgba(0,0,0,0.1);
            border-radius: 6px;
            overflow: hidden;
        }
        
        .language-option {
            padding: 0.3rem 0.6rem;
            background: transparent;
            border: none;
            cursor: pointer;
            font-size: 0.7rem;
            font-weight: 600;
            color: #6c757d;
            transition: all 0.2s ease;
        }
        
        .language-option.active {
            background: #667eea;
            color: white;
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
"""

READER_TOOLS_HTML = """
        <!-- Reader Tools -->
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
            
            <div class="language-switcher">
                <button class="language-option active">IT</button>
                <button class="language-option" onclick="switchLanguage('en')">EN</button>
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
        </div>"""

READER_TOOLS_JS = """
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
                newPath = currentPath.replace('/it/', '/en/').replace(/filosofia-core-architettura/, 'core-philosophy-architecture');
            } else {
                newPath = currentPath.replace('/en/', '/it/').replace(/core-philosophy-architecture/, 'filosofia-core-architettura');
            }
            
            window.location.href = newPath;
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
        }"""

def add_reader_tools_to_file(file_path):
    """Add reader tools to a single HTML file"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if reader tools are already present
    if '.reader-tools' in content:
        return False
    
    # Add CSS before closing </style> tag
    style_pattern = r'(\s*)(</style>\s*</head>)'
    style_match = re.search(style_pattern, content)
    
    if not style_match:
        print(f"✗ Could not find closing </style> tag in: {file_path}")
        return False
    
    # Insert CSS
    indent = style_match.group(1)
    css_replacement = f"{READER_TOOLS}\n{indent}{style_match.group(2)}"
    content = re.sub(style_pattern, css_replacement, content)
    
    # Add HTML before closing </body> tag
    html_pattern = r'(\s*)(</body>\s*</html>)'
    html_match = re.search(html_pattern, content)
    
    if not html_match:
        print(f"✗ Could not find closing </body> tag in: {file_path}")
        return False
    
    # Insert HTML and JavaScript
    indent = html_match.group(1)
    js_with_html = f"""
{READER_TOOLS_HTML}

    <script>
{READER_TOOLS_JS}
    </script>

{indent}{html_match.group(2)}"""
    
    content = re.sub(html_pattern, js_with_html, content)
    
    # Write updated content back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def find_chapter_html_files(base_dir):
    """Find all chapter HTML files (excluding index/navigation pages)"""
    
    html_files = []
    pattern = os.path.join(base_dir, "**/index.html")
    
    for file_path in glob.glob(pattern, recursive=True):
        # Skip main index files and focus on chapter files
        if '/filosofia-core-architettura/index.html' in file_path:
            continue
        if '/ai-team-orchestrator.html' in file_path:
            continue
        if '/libro.html' in file_path:
            continue
        if '/book.html' in file_path:
            continue
        
        # Only include files that are in chapter subdirectories
        if file_path.count('/') > base_dir.count('/') + 1:
            html_files.append(file_path)
    
    return html_files

def main():
    base_dir = "/Users/pelleri/Documents/ai-team-orchestrator/ebook/web"
    
    print("🛠️ Adding reader experience tools to chapter files...")
    html_files = find_chapter_html_files(base_dir)
    
    print(f"📊 Found {len(html_files)} chapter files to update")
    
    updated_count = 0
    for file_path in html_files:
        if add_reader_tools_to_file(file_path):
            print(f"✓ Added reader tools to: {os.path.relpath(file_path, base_dir)}")
            updated_count += 1
        else:
            print(f"⚠ Skipped (already has tools): {os.path.relpath(file_path, base_dir)}")
    
    print(f"\n✅ COMPLETED: Added reader tools to {updated_count} files")
    print(f"📄 Total files processed: {len(html_files)}")
    
    print("\n🎯 Reader Tools Features Added:")
    print("• 🌙 Dark/Light theme toggle with persistence")
    print("• 🔖 Bookmark system with local storage")  
    print("• 🌐 Language switcher (ITA/ENG)")
    print("• 📊 Reading progress tracker")
    print("• 🔤 Font size adjustment")
    print("• ⚙️ Collapsible tools panel")
    print("• 📱 Mobile responsive design")
    print("• 💾 All preferences saved locally")

if __name__ == "__main__":
    main()