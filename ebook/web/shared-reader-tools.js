/**
 * AI Team Orchestrator - Optimized Reader Tools
 * Performance-optimized JavaScript for better Core Web Vitals
 * Mobile-first touch interface support
 */

class OptimizedReaderTools {
    constructor() {
        this.isScrolling = false;
        this.currentFontSize = 16;
        this.theme = 'light';
        this.bookmarks = [];
        
        this.init();
    }
    
    init() {
        // Wait for DOM to be fully loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupTools());
        } else {
            this.setupTools();
        }
    }
    
    setupTools() {
        this.loadUserPreferences();
        this.initializeProgressBar();
        this.initializeReaderButtons();
        this.initializeKeyboardShortcuts();
        this.initializeAccessibility();
    }
    
    loadUserPreferences() {
        // Load saved theme
        const savedTheme = localStorage.getItem('ato_theme');
        if (savedTheme) {
            this.theme = savedTheme;
            document.body.classList.toggle('dark-mode', savedTheme === 'dark');
        }
        
        // Load saved font size
        const savedFontSize = localStorage.getItem('ato_fontSize');
        if (savedFontSize) {
            this.currentFontSize = parseInt(savedFontSize);
            document.body.style.fontSize = this.currentFontSize + 'px';
        }
        
        // Load bookmarks
        const savedBookmarks = localStorage.getItem('ato_bookmarks');
        if (savedBookmarks) {
            try {
                this.bookmarks = JSON.parse(savedBookmarks);
            } catch (e) {
                console.warn('Failed to parse saved bookmarks:', e);
                this.bookmarks = [];
            }
        }
    }
    
    initializeProgressBar() {
        // Throttled scroll handler for better performance
        const updateProgress = () => {
            if (!this.isScrolling) {
                requestAnimationFrame(() => {
                    const winScroll = document.body.scrollTop || document.documentElement.scrollTop;
                    const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
                    const scrolled = Math.min(100, Math.max(0, (winScroll / height) * 100));
                    
                    const progressFill = document.getElementById('progressFill');
                    if (progressFill) {
                        progressFill.style.width = scrolled + '%';
                    }
                    
                    this.isScrolling = false;
                });
                this.isScrolling = true;
            }
        };
        
        // Use passive event listeners for better performance
        document.addEventListener('scroll', updateProgress, { passive: true });
        
        // Initialize progress bar
        updateProgress();
    }
    
    initializeReaderButtons() {
        const buttons = [
            { id: 'bookmarkBtn', handler: () => this.toggleBookmark() },
            { id: 'themeBtn', handler: () => this.toggleTheme() },
            { id: 'fontBtn', handler: () => this.adjustFontSize() },
            { id: 'shareBtn', handler: () => this.shareChapter() },
            { id: 'settingsBtn', handler: () => this.openSettings() }
        ];
        
        buttons.forEach(({ id, handler }) => {
            const button = document.getElementById(id);
            if (button) {
                // Add touch-optimized event listeners
                button.addEventListener('click', handler);
                
                // Prevent double-tap zoom on iOS
                button.addEventListener('touchstart', (e) => {
                    e.preventDefault();
                    button.style.transform = 'scale(0.95)';
                });
                
                button.addEventListener('touchend', (e) => {
                    e.preventDefault();
                    button.style.transform = '';
                    handler();
                });
                
                // Add proper ARIA attributes
                button.setAttribute('role', 'button');
                button.setAttribute('tabindex', '0');
            }
        });
        
        // Close modal handlers
        document.querySelectorAll('.close-button').forEach(button => {
            button.addEventListener('click', () => this.closeModal());
        });
        
        // Close modal when clicking outside
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.closeModal();
            }
        });
    }
    
    initializeKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ignore if user is typing in an input
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return;
            }
            
            switch (e.key) {
                case 'b':
                case 'B':
                    this.toggleBookmark();
                    e.preventDefault();
                    break;
                case 't':
                case 'T':
                    this.toggleTheme();
                    e.preventDefault();
                    break;
                case '+':
                case '=':
                    this.adjustFontSize(2);
                    e.preventDefault();
                    break;
                case '-':
                    this.adjustFontSize(-2);
                    e.preventDefault();
                    break;
                case 'Escape':
                    this.closeModal();
                    break;
            }
        });
    }
    
    initializeAccessibility() {
        // Focus management for modals
        document.addEventListener('keydown', (e) => {
            const modal = document.querySelector('.modal.show');
            if (modal && e.key === 'Tab') {
                this.trapFocus(modal, e);
            }
        });
    }
    
    toggleBookmark() {
        const currentUrl = window.location.href;
        const currentTitle = document.title;
        const bookmarkIndex = this.bookmarks.findIndex(b => b.url === currentUrl);
        
        if (bookmarkIndex > -1) {
            // Remove bookmark
            this.bookmarks.splice(bookmarkIndex, 1);
            this.showToast('Bookmark removed!', 'info');
            this.updateBookmarkButton(false);
        } else {
            // Add bookmark
            this.bookmarks.push({
                url: currentUrl,
                title: currentTitle,
                date: new Date().toISOString()
            });
            this.showToast('Bookmark saved!', 'success');
            this.updateBookmarkButton(true);
        }
        
        // Save to localStorage
        localStorage.setItem('ato_bookmarks', JSON.stringify(this.bookmarks));
        
        // Analytics tracking
        if (typeof gtag !== 'undefined') {
            gtag('event', 'bookmark_toggle', {
                'page_title': currentTitle,
                'page_location': currentUrl,
                'action': bookmarkIndex > -1 ? 'remove' : 'add'
            });
        }
    }
    
    updateBookmarkButton(isBookmarked) {
        const button = document.getElementById('bookmarkBtn');
        if (button) {
            button.textContent = isBookmarked ? '🔖' : '📖';
            button.setAttribute('aria-pressed', isBookmarked.toString());
            button.title = isBookmarked ? 'Remove bookmark' : 'Add bookmark';
        }
    }
    
    toggleTheme() {
        this.theme = this.theme === 'light' ? 'dark' : 'light';
        document.body.classList.toggle('dark-mode', this.theme === 'dark');
        
        // Update theme button
        const button = document.getElementById('themeBtn');
        if (button) {
            button.textContent = this.theme === 'dark' ? '☀️' : '🌙';
            button.title = `Switch to ${this.theme === 'dark' ? 'light' : 'dark'} theme`;
        }
        
        // Save preference
        localStorage.setItem('ato_theme', this.theme);
        
        this.showToast(`${this.theme === 'dark' ? 'Dark' : 'Light'} theme activated`, 'info');
        
        // Analytics tracking
        if (typeof gtag !== 'undefined') {
            gtag('event', 'theme_toggle', {
                'theme': this.theme
            });
        }
    }
    
    adjustFontSize(change = 2) {
        const minSize = 12;
        const maxSize = 24;
        
        this.currentFontSize = Math.max(minSize, Math.min(maxSize, this.currentFontSize + change));
        document.body.style.fontSize = this.currentFontSize + 'px';
        
        // Save preference
        localStorage.setItem('ato_fontSize', this.currentFontSize.toString());
        
        // Update button text
        const button = document.getElementById('fontBtn');
        if (button) {
            button.title = `Font size: ${this.currentFontSize}px`;
        }
        
        this.showToast(`Font size: ${this.currentFontSize}px`, 'info');
    }
    
    shareChapter() {
        const shareData = {
            title: document.title,
            url: window.location.href,
            text: document.querySelector('meta[name="description"]')?.content || ''
        };
        
        if (navigator.share && /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
            navigator.share(shareData).then(() => {
                this.showToast('Chapter shared!', 'success');
            }).catch(err => {
                console.log('Error sharing:', err);
                this.fallbackShare(shareData.url);
            });
        } else {
            this.fallbackShare(shareData.url);
        }
        
        // Analytics tracking
        if (typeof gtag !== 'undefined') {
            gtag('event', 'share', {
                'method': 'reader_tools',
                'page_title': shareData.title,
                'page_location': shareData.url
            });
        }
    }
    
    fallbackShare(url) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(url).then(() => {
                this.showToast('Link copied to clipboard!', 'success');
            }).catch(() => {
                this.showToast('Failed to copy link', 'error');
            });
        } else {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = url;
            document.body.appendChild(textArea);
            textArea.select();
            
            try {
                document.execCommand('copy');
                this.showToast('Link copied to clipboard!', 'success');
            } catch (err) {
                this.showToast('Failed to copy link', 'error');
            }
            
            document.body.removeChild(textArea);
        }
    }
    
    openSettings() {
        const modal = document.getElementById('settingsModal');
        if (modal) {
            modal.classList.add('show');
            modal.setAttribute('aria-hidden', 'false');
            
            // Focus first focusable element
            const firstFocusable = modal.querySelector('button, input, select, textarea, [tabindex]:not([tabindex="-1"])');
            if (firstFocusable) {
                firstFocusable.focus();
            }
        }
    }
    
    closeModal() {
        const modal = document.querySelector('.modal.show');
        if (modal) {
            modal.classList.remove('show');
            modal.setAttribute('aria-hidden', 'true');
            
            // Return focus to trigger button
            const triggerButton = document.getElementById('settingsBtn');
            if (triggerButton) {
                triggerButton.focus();
            }
        }
    }
    
    showToast(message, type = 'info') {
        const toast = document.getElementById('toast');
        if (!toast) return;
        
        // Remove existing classes
        toast.className = 'toast';
        toast.textContent = message;
        
        // Add type-specific class
        if (type === 'success') toast.classList.add('toast-success');
        else if (type === 'error') toast.classList.add('toast-error');
        else if (type === 'warning') toast.classList.add('toast-warning');
        
        // Show toast
        toast.classList.add('show');
        
        // Auto-hide after 3 seconds
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }
    
    trapFocus(modal, event) {
        const focusableElements = modal.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const firstFocusable = focusableElements[0];
        const lastFocusable = focusableElements[focusableElements.length - 1];
        
        if (event.shiftKey) {
            if (document.activeElement === firstFocusable) {
                lastFocusable.focus();
                event.preventDefault();
            }
        } else {
            if (document.activeElement === lastFocusable) {
                firstFocusable.focus();
                event.preventDefault();
            }
        }
    }
    
    // Initialize bookmark button state on load
    updateBookmarkState() {
        const currentUrl = window.location.href;
        const isBookmarked = this.bookmarks.some(b => b.url === currentUrl);
        this.updateBookmarkButton(isBookmarked);
    }
}

// Initialize reader tools when DOM is ready
(() => {
    if (typeof window !== 'undefined') {
        window.readerTools = new OptimizedReaderTools();
        
        // Initialize bookmark state after tools are loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                setTimeout(() => window.readerTools.updateBookmarkState(), 100);
            });
        } else {
            setTimeout(() => window.readerTools.updateBookmarkState(), 100);
        }
    }
})();