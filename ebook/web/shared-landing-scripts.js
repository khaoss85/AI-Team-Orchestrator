/* 🔧 Shared Landing Page Scripts */
/* Language detection and auto-redirect functionality */

class LanguageDetector {
    constructor() {
        this.supportedLanguages = ['it', 'en'];
        this.fallbackLanguage = 'it';
        this.init();
    }
    
    init() {
        // Always perform auto-detection and redirect
        this.detectAndRedirect();
    }
    
    detectAndRedirect() {
        const detectedLang = this.detectLanguage();
        
        if (detectedLang && this.isSupported(detectedLang)) {
            // Show detection message
            document.getElementById('detecting').style.display = 'block';
            
            // Auto-redirect after 1 second
            setTimeout(() => {
                this.redirect(detectedLang);
            }, 1000);
        }
    }
    
    detectLanguage() {
        // Check URL parameters first
        const urlParams = new URLSearchParams(window.location.search);
        const langParam = urlParams.get('lang');
        if (langParam && this.isSupported(langParam)) {
            return langParam;
        }
        
        // Browser language detection
        const browserLang = navigator.language || navigator.userLanguage;
        
        if (browserLang) {
            // Extract primary language (e.g., 'it' from 'it-IT')
            const primaryLang = browserLang.toLowerCase().split('-')[0];
            return this.isSupported(primaryLang) ? primaryLang : null;
        }
        
        return null;
    }
    
    isSupported(lang) {
        return this.supportedLanguages.includes(lang.toLowerCase());
    }
    
    redirect(lang) {
        // Determine the correct path based on current location
        let basePath = '';
        
        // If we're in a subdirectory, adjust the path
        const currentPath = window.location.pathname;
        if (currentPath !== '/') {
            basePath = currentPath.replace(/\/[^\/]*$/, '/');
        }
        
        // Redirect to the language-specific version
        const targetUrl = `${basePath}${lang}/`;
        window.location.href = targetUrl;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize auto-detection if we're on the language selection page
    if (document.querySelector('.language-selector')) {
        new LanguageDetector();
    }
});

// Analytics tracking (if needed)
function trackLanguageSelection(language) {
    if (typeof gtag !== 'undefined') {
        gtag('event', 'language_selection', {
            'language': language,
            'page_title': 'Language Selection'
        });
    }
}