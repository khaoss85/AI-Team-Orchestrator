/**
 * 🌍 AI Team Orchestrator - Multilingual Engine
 * Enterprise-grade i18n system for scalable book translations
 */

class MultilingualEngine {
    constructor() {
        this.supportedLanguages = [
            { code: 'it', name: 'Italiano', flag: '🇮🇹', dir: 'ltr' },
            { code: 'en', name: 'English', flag: '🇬🇧', dir: 'ltr' },
            { code: 'es', name: 'Español', flag: '🇪🇸', dir: 'ltr' },
            { code: 'fr', name: 'Français', flag: '🇫🇷', dir: 'ltr' }
        ];
        
        this.fallbackLang = 'it';
        this.translations = {};
        this.currentLang = this.detectLanguage();
        
        this.init();
    }
    
    async init() {
        try {
            await this.loadTranslations();
            this.setupLanguageSwitcher();
            this.applyTranslations();
            this.updateMetaTags();
            this.trackLanguage();
        } catch (error) {
            console.error('MultilingualEngine initialization failed:', error);
        }
    }
    
    detectLanguage() {
        // Priority: URL > localStorage > Navigator > Geo-IP > Default
        
        // 1. Check URL path (/it/, /en/, etc.)
        const urlMatch = window.location.pathname.match(/\/([a-z]{2})\//);
        if (urlMatch && this.isSupported(urlMatch[1])) {
            return urlMatch[1];
        }
        
        // 2. Check localStorage
        const saved = localStorage.getItem('preferred_language');
        if (saved && this.isSupported(saved)) {
            return saved;
        }
        
        // 3. Check browser language
        const browser = navigator.language.substring(0, 2);
        if (this.isSupported(browser)) {
            return browser;
        }
        
        // 4. Default fallback
        return this.fallbackLang;
    }
    
    isSupported(langCode) {
        return this.supportedLanguages.some(lang => lang.code === langCode);
    }
    
    async loadTranslations() {
        const baseUrl = this.getBaseUrl();
        
        try {
            const [ui, meta, landing] = await Promise.all([
                fetch(`${baseUrl}/translations/ui.json`).then(r => r.json()),
                fetch(`${baseUrl}/translations/meta.json`).then(r => r.json()),
                fetch(`${baseUrl}/translations/landing.json`).then(r => r.json())
            ]);
            
            this.translations = { ui, meta, landing };
            console.log(`✅ Translations loaded for languages:`, Object.keys(ui));
            
        } catch (error) {
            console.warn('Translation loading failed, using fallback:', error);
            this.translations = this.getFallbackTranslations();
        }
    }
    
    getBaseUrl() {
        // Handle both development and production URLs
        const path = window.location.pathname;
        if (path.includes('/it/') || path.includes('/en/') || 
            path.includes('/es/') || path.includes('/fr/')) {
            return '../..';
        }
        return '.';
    }
    
    getFallbackTranslations() {
        return {
            ui: {
                nav: {
                    it: { previousChapter: "← Capitolo Precedente", nextChapter: "Capitolo Successivo →" },
                    en: { previousChapter: "← Previous Chapter", nextChapter: "Next Chapter →" }
                }
            },
            meta: {},
            landing: {}
        };
    }
    
    t(key, params = {}) {
        const keys = key.split('.');
        let value = this.translations;
        
        // Navigate through nested object
        for (const k of keys) {
            if (value && typeof value === 'object') {
                value = value[k];
            } else {
                break;
            }
        }
        
        // Get translation for current language
        if (value && typeof value === 'object') {
            const translation = value[this.currentLang] || 
                              value[this.fallbackLang] || 
                              key;
            
            return this.interpolate(translation, params);
        }
        
        return key; // Return key if translation not found
    }
    
    interpolate(text, params) {
        if (typeof text !== 'string') return text;
        
        return text.replace(/\{\{(\w+)\}\}/g, (match, key) => {
            return params[key] || match;
        });
    }
    
    switchLanguage(newLang) {
        if (!this.isSupported(newLang)) {
            console.warn(`Language ${newLang} not supported`);
            return;
        }
        
        // Save preference
        localStorage.setItem('preferred_language', newLang);
        
        // Analytics tracking
        this.trackLanguageSwitch(this.currentLang, newLang);
        
        // Smart URL rewriting
        const currentPath = window.location.pathname;
        let newPath;
        
        if (currentPath.match(/\/([a-z]{2})\//)) {
            // Replace existing language in path
            newPath = currentPath.replace(/\/([a-z]{2})\//, `/${newLang}/`);
        } else {
            // Add language to path
            newPath = `/${newLang}${currentPath}`;
        }
        
        // Preserve query parameters and hash
        const search = window.location.search;
        const hash = window.location.hash;
        
        window.location.href = newPath + search + hash;
    }
    
    setupLanguageSwitcher() {
        // Create language switcher if it doesn't exist
        if (!document.getElementById('language-switcher')) {
            this.createLanguageSwitcher();
        }
        
        // Setup event listeners
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('lang-switch-btn')) {
                const lang = e.target.dataset.lang;
                this.switchLanguage(lang);
            }
        });
    }
    
    createLanguageSwitcher() {
        const switcher = document.createElement('div');
        switcher.id = 'language-switcher';
        switcher.className = 'language-switcher';
        
        const buttons = this.supportedLanguages.map(lang => `
            <button class="lang-switch-btn ${lang.code === this.currentLang ? 'active' : ''}" 
                    data-lang="${lang.code}"
                    title="${lang.name}">
                ${lang.flag} ${lang.code.toUpperCase()}
            </button>
        `).join('');
        
        switcher.innerHTML = `
            <div class="lang-switcher-label">🌍</div>
            <div class="lang-switcher-buttons">
                ${buttons}
            </div>
        `;
        
        // Insert into header or create floating switcher
        const header = document.querySelector('header, .header, .top-bar');
        if (header) {
            header.appendChild(switcher);
        } else {
            // Create floating switcher
            switcher.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 12px;
                padding: 8px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
                display: flex;
                align-items: center;
                gap: 8px;
            `;
            document.body.appendChild(switcher);
        }
    }
    
    applyTranslations() {
        // Apply translations to elements with data-i18n attributes
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translated = this.t(key);
            
            if (element.tagName === 'INPUT' && element.type === 'submit') {
                element.value = translated;
            } else if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                element.placeholder = translated;
            } else {
                element.textContent = translated;
            }
        });
        
        // Apply HTML translations (for elements with data-i18n-html)
        document.querySelectorAll('[data-i18n-html]').forEach(element => {
            const key = element.getAttribute('data-i18n-html');
            const translated = this.t(key);
            element.innerHTML = translated;
        });
    }
    
    updateMetaTags() {
        const meta = this.translations.meta;
        if (!meta || !meta[this.currentLang]) return;
        
        const langMeta = meta[this.currentLang];
        
        // Update title
        if (langMeta.title) {
            document.title = langMeta.title;
        }
        
        // Update description
        const descMeta = document.querySelector('meta[name="description"]');
        if (descMeta && langMeta.description) {
            descMeta.content = langMeta.description;
        }
        
        // Update Open Graph tags
        ['og:title', 'og:description', 'og:locale'].forEach(property => {
            const meta = document.querySelector(`meta[property="${property}"]`);
            const key = property.replace('og:', '').replace(':', '_');
            if (meta && langMeta[key]) {
                meta.content = langMeta[key];
            }
        });
        
        // Update html lang attribute
        document.documentElement.lang = this.currentLang;
        
        // Update canonical and alternate links
        this.updateAlternateLinks();
    }
    
    updateAlternateLinks() {
        // Remove existing alternate links
        document.querySelectorAll('link[rel="alternate"][hreflang]').forEach(link => {
            link.remove();
        });
        
        // Add alternate links for all supported languages
        this.supportedLanguages.forEach(lang => {
            const link = document.createElement('link');
            link.rel = 'alternate';
            link.hreflang = lang.code;
            
            const currentPath = window.location.pathname;
            const basePath = currentPath.replace(/\/([a-z]{2})\//, '/');
            link.href = `${window.location.origin}/${lang.code}${basePath}`;
            
            document.head.appendChild(link);
        });
        
        // Update canonical link
        let canonical = document.querySelector('link[rel="canonical"]');
        if (!canonical) {
            canonical = document.createElement('link');
            canonical.rel = 'canonical';
            document.head.appendChild(canonical);
        }
        
        const currentPath = window.location.pathname;
        canonical.href = `${window.location.origin}${currentPath}`;
    }
    
    trackLanguage() {
        // Track language usage for analytics
        if (typeof gtag !== 'undefined') {
            gtag('event', 'language_detected', {
                'language': this.currentLang,
                'method': 'auto_detection'
            });
        }
        
        // Store in sessionStorage for other scripts
        sessionStorage.setItem('current_language', this.currentLang);
    }
    
    trackLanguageSwitch(fromLang, toLang) {
        if (typeof gtag !== 'undefined') {
            gtag('event', 'language_switch', {
                'from_language': fromLang,
                'to_language': toLang,
                'page_type': this.getPageType()
            });
        }
        
        console.log(`Language switched: ${fromLang} → ${toLang}`);
    }
    
    getPageType() {
        const path = window.location.pathname;
        if (path.includes('libro') || path.includes('book')) return 'book';
        if (path.includes('indice') || path.includes('table')) return 'toc';
        return 'landing';
    }
    
    // Utility methods for external use
    getCurrentLanguage() {
        return this.currentLang;
    }
    
    getSupportedLanguages() {
        return this.supportedLanguages;
    }
    
    isRTL() {
        const lang = this.supportedLanguages.find(l => l.code === this.currentLang);
        return lang ? lang.dir === 'rtl' : false;
    }
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.i18n = new MultilingualEngine();
    });
} else {
    window.i18n = new MultilingualEngine();
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MultilingualEngine;
}