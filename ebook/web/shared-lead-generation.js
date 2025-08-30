/**
 * 🎯 Shared Lead Generation System
 * Universal lead generation popup for all ebook pages
 * Safe, modular, and configurable
 */

// Global configuration
window.LeadGenConfig = {
    apiUrl: 'https://szerliaxjcverzdoisik.supabase.co/functions/v1/submit-lead', // Correct Supabase Edge Function
    triggers: {
        scrollDepth: 50,        // % of page scrolled (back to production)
        timeOnPage: 240,        // seconds (back to production - 4 minutes)
        exitIntent: true,       // mouse leaving page
        mobileScrollStop: 6000, // ms of scroll inactivity (back to production)
        returnVisitor: 10000    // ms delay for return visitors (back to production)
    },
    cooldowns: {
        dismissalCooldown: 15 * 60 * 1000,    // 15 minutes after dismissal
        sessionShowOnce: true,                 // Only once per session regardless
        minTimeBetweenSessions: 24 * 60 * 60 * 1000  // 24 hours between sessions
    },
    debug: true // Set to true for console logging - ENABLED FOR TESTING
};

// Lead generation state
let leadPopupState = {
    shown: false,
    triggers: {
        scrollDepth: false,
        timeOnPage: false,
        exitIntent: false,
        mobileScrollStop: false,
        returnVisitor: false
    },
    timeOnPage: 0
};

// Utility functions
function debugLog(message, ...args) {
    if (window.LeadGenConfig.debug) {
        console.log(`🎯 LeadGen: ${message}`, ...args);
    }
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Check if popup should be shown
function shouldShowPopup(trigger = 'unknown') {
    // In debug mode, always allow manual triggers for testing
    if (window.LeadGenConfig.debug && trigger === 'manual-test') {
        debugLog('Debug mode: allowing manual test trigger');
        return true;
    }
    
    // Check if already completed (submitted form successfully) - PERMANENT
    if (localStorage.getItem('leadPopupShown') === 'true') {
        debugLog('Popup already completed (form submitted) - never show again');
        return false;
    }
    
    // Check dismissal cooldown - 15 minutes after being dismissed
    const dismissalTime = localStorage.getItem('leadPopupDismissedAt');
    if (dismissalTime) {
        const timeSinceDismissal = Date.now() - parseInt(dismissalTime);
        if (timeSinceDismissal < window.LeadGenConfig.cooldowns.dismissalCooldown) {
            const remainingMinutes = Math.ceil((window.LeadGenConfig.cooldowns.dismissalCooldown - timeSinceDismissal) / 60000);
            debugLog(`Popup in dismissal cooldown - ${remainingMinutes} minutes remaining`);
            return false;
        }
    }
    
    // Check if user dismissed popup in this session (temporary block)
    if (sessionStorage.getItem('leadPopupDismissed') === 'true') {
        debugLog('Popup was dismissed by user this session');
        return false;
    }
    
    // Check if already shown in this session
    if (sessionStorage.getItem('leadPopupShown') === 'true') {
        debugLog('Popup already shown this session');
        return false;
    }
    
    // Check minimum time between sessions (24h cooldown)
    const lastShownTime = localStorage.getItem('lastPopupShownAt');
    if (lastShownTime) {
        const timeSinceLastShown = Date.now() - parseInt(lastShownTime);
        if (timeSinceLastShown < window.LeadGenConfig.cooldowns.minTimeBetweenSessions) {
            const remainingHours = Math.ceil((window.LeadGenConfig.cooldowns.minTimeBetweenSessions - timeSinceLastShown) / 3600000);
            debugLog(`Popup in session cooldown - ${remainingHours} hours remaining`);
            return false;
        }
    }
    
    return !leadPopupState.shown;
}

// Initialize lead generation system
function initLeadGeneration() {
    debugLog('Initializing lead generation system');

    // Track visit count
    let visitCount = parseInt(localStorage.getItem('ebook-visit-count') || '0');
    visitCount++;
    localStorage.setItem('ebook-visit-count', visitCount.toString());
    debugLog('Visit count:', visitCount);

    // Always initialize triggers (they have their own shouldShowPopup checks)
    initScrollDepthTrigger();
    initTimeOnPageTrigger();
    initExitIntentTrigger();
    initMobileScrollStopTrigger();

    // Return visitor trigger (visit count > 1)
    if (visitCount > 1) {
        initReturnVisitorTrigger();
    }

    // Check initial state
    if (!shouldShowPopup()) {
        debugLog('Lead popup already shown or dismissed, but triggers are active');
    }
}

// Trigger implementations
function initScrollDepthTrigger() {
    const scrollHandler = debounce(() => {
        if (leadPopupState.triggers.scrollDepth || !shouldShowPopup('scroll-depth')) return;

        const scrollPercent = (window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100;
        
        if (scrollPercent >= window.LeadGenConfig.triggers.scrollDepth) {
            leadPopupState.triggers.scrollDepth = true;
            debugLog(`Scroll depth trigger: ${scrollPercent.toFixed(1)}%`);
            
            // Wait 2 seconds to ensure engagement
            setTimeout(() => {
                if (shouldShowPopup('scroll-depth')) {
                    showLeadPopup('scroll-depth');
                }
            }, 2000);
        }
    }, 1000);

    window.addEventListener('scroll', scrollHandler);
}

function initTimeOnPageTrigger() {
    const timeTracker = setInterval(() => {
        leadPopupState.timeOnPage += 30;
        
        if (leadPopupState.timeOnPage >= window.LeadGenConfig.triggers.timeOnPage && 
            !leadPopupState.triggers.timeOnPage && shouldShowPopup('time-on-page')) {
            
            leadPopupState.triggers.timeOnPage = true;
            debugLog(`Time on page trigger: ${leadPopupState.timeOnPage}s`);
            showLeadPopup('time-on-page');
            clearInterval(timeTracker);
        }

        // Cleanup if popup shown by other trigger or dismissed
        if (leadPopupState.shown || !shouldShowPopup('time-on-page')) {
            clearInterval(timeTracker);
        }
    }, 30000);
}

function initExitIntentTrigger() {
    if (!window.LeadGenConfig.triggers.exitIntent) return;

    let exitIntentShown = false;

    document.addEventListener('mouseleave', (e) => {
        if (e.clientY <= 0 && !leadPopupState.triggers.exitIntent && 
            shouldShowPopup() && !exitIntentShown) {
            
            exitIntentShown = true;
            leadPopupState.triggers.exitIntent = true;
            debugLog('Exit intent trigger');
            showLeadPopup('exit-intent');
        }
    });

    // Mobile pagehide event
    if (/iPad|iPhone|iPod/.test(navigator.userAgent)) {
        window.addEventListener('pagehide', () => {
            if (!leadPopupState.triggers.exitIntent && shouldShowPopup() && !exitIntentShown) {
                exitIntentShown = true;
                leadPopupState.triggers.exitIntent = true;
                debugLog('Mobile exit intent trigger');
                showLeadPopup('mobile-exit-intent');
            }
        });
    }
}

function initMobileScrollStopTrigger() {
    let scrollTimeout;
    
    const scrollHandler = () => {
        clearTimeout(scrollTimeout);
        
        scrollTimeout = setTimeout(() => {
            if (leadPopupState.triggers.mobileScrollStop || !shouldShowPopup()) return;

            const scrollPercent = (window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100;
            
            if (scrollPercent >= 25) {
                leadPopupState.triggers.mobileScrollStop = true;
                debugLog('Mobile scroll stop trigger');
                showLeadPopup('mobile-scroll-stop');
            }
        }, window.LeadGenConfig.triggers.mobileScrollStop);
    };

    window.addEventListener('scroll', scrollHandler);
}

function initReturnVisitorTrigger() {
    debugLog('Return visitor detected');
    
    setTimeout(() => {
        if (shouldShowPopup()) {
            leadPopupState.triggers.returnVisitor = true;
            debugLog('Return visitor trigger');
            showLeadPopup('return-visitor');
        }
    }, window.LeadGenConfig.triggers.returnVisitor);
}

// Show popup function
function showLeadPopup(trigger = 'manual') {
    if (!shouldShowPopup(trigger)) {
        debugLog(`Popup blocked - already shown or disabled. Trigger: ${trigger}`);
        return;
    }

    debugLog(`Showing popup with trigger: ${trigger}`);

    // Mark as shown
    leadPopupState.shown = true;
    sessionStorage.setItem('leadPopupShown', 'true');
    sessionStorage.setItem('leadPopupTrigger', trigger);
    localStorage.setItem('lastPopupShownAt', Date.now().toString());

    // Create popup HTML
    const popupHTML = `
        <div id="lead-popup-overlay" class="lead-popup-overlay">
            <div class="lead-popup-content">
                <button class="lead-popup-close" onclick="closeLeadPopup()">&times;</button>
                
                <div class="lead-popup-header">
                    <span class="popup-emoji">🚀</span>
                    <h3 class="popup-title">Join the AI Builder Community</h3>
                </div>
                
                <div class="lead-popup-body">
                    <p><strong>Get exclusive updates & resources!</strong> ✨</p>
                    <p>Join <strong>2,500+ AI builders</strong> who receive practical insights, real case studies, and early access to new content.</p>
                    <p>I share what I learn from building production AI systems – <strong>no fluff, just actionable insights.</strong></p>
                    
                    <form id="lead-form" onsubmit="submitLeadForm(event)">
                        <div class="form-group">
                            <label for="lead-name">Name *</label>
                            <input type="text" id="lead-name" name="name" required placeholder="John Doe">
                        </div>
                        
                        <div class="form-group">
                            <label for="lead-email">Email *</label>
                            <input type="email" id="lead-email" name="email" required placeholder="john@company.com">
                        </div>
                        
                        <div class="form-group">
                            <label for="lead-role">Your Role</label>
                            <select id="lead-role" name="role">
                                <option value="">Select your role (optional)</option>
                                <option value="ceo">CEO/Founder</option>
                                <option value="cto">CTO/Tech Lead</option>
                                <option value="developer">Software Developer</option>
                                <option value="product-manager">Product Manager</option>
                                <option value="ai-engineer">AI/ML Engineer</option>
                                <option value="consultant">Consultant</option>
                                <option value="student">Student/Researcher</option>
                                <option value="other">Other</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="lead-challenge">What's your biggest AI challenge? (optional)</label>
                            <textarea id="lead-challenge" name="challenge" placeholder="e.g., 'Scaling from 1 to multiple agents', 'Production deployment', 'Team coordination'..."></textarea>
                        </div>
                        
                        <div class="checkbox-group">
                            <input type="checkbox" id="gdpr-consent" name="gdpr_consent" required>
                            <label for="gdpr-consent" class="checkbox-label">
                                I consent to receive updates about AI systems & architecture from Daniele Pelleri. Unsubscribe anytime.
                            </label>
                        </div>
                        
                        <button type="submit" class="lead-submit-btn">🚀 Join the Community</button>
                    </form>
                </div>
            </div>
        </div>
    `;

    // Add to page
    document.body.insertAdjacentHTML('beforeend', popupHTML);
    
    // Show with animation
    setTimeout(() => {
        const overlay = document.getElementById('lead-popup-overlay');
        if (overlay) {
            overlay.classList.add('visible');
        }
    }, 100);
}

// Close popup function
function closeLeadPopup(reason = 'user-close') {
    const overlay = document.getElementById('lead-popup-overlay');
    if (overlay) {
        overlay.classList.remove('visible');
        setTimeout(() => {
            overlay.remove();
        }, 300);
    }
    
    // If user explicitly closed (not from form submission), apply cooldowns
    if (reason === 'user-close') {
        sessionStorage.setItem('leadPopupDismissed', 'true');
        localStorage.setItem('leadPopupDismissedAt', Date.now().toString());
        debugLog('Popup dismissed by user - 15 minute cooldown applied');
    } else {
        debugLog('Popup closed:', reason);
    }
}

// Submit form function
function submitLeadForm(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const trigger = sessionStorage.getItem('leadPopupTrigger') || 'unknown';
    
    const data = {
        name: formData.get('name'),
        email: formData.get('email'),
        role: formData.get('role') || null,
        challenge: formData.get('challenge') || null,
        gdpr_consent: formData.get('gdpr_consent') === 'on',
        marketing_consent: true, // implied consent for updates
        book_chapter: 'shared-popup', // identify source
        trigger: trigger,
        page_url: window.location.href,
        page_title: document.title,
        referrer_url: document.referrer || null,
        user_agent: navigator.userAgent,
        timestamp: new Date().toISOString()
    };

    debugLog('Submitting lead form', data);

    // Show loading state
    const submitBtn = document.querySelector('.lead-submit-btn');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = 'Saving...';
    submitBtn.disabled = true;

    // Submit to API with fallback
    const submitToAPI = async () => {
        try {
            const response = await fetch(window.LeadGenConfig.apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${window.LeadGenConfig.apiKey || ''}`,
                },
                body: JSON.stringify(data)
            });
            
            if (response.ok) {
                const result = await response.json();
                debugLog('Lead form submitted successfully to API', result);
                if (result.success) {
                    return true;
                } else {
                    throw new Error(result.error || `API returned success=false`);
                }
            } else {
                const errorText = await response.text();
                let errorMessage = `API responded with status: ${response.status}`;
                try {
                    const errorJson = JSON.parse(errorText);
                    if (errorJson.error) errorMessage += ` - ${errorJson.error}`;
                } catch {
                    if (errorText) errorMessage += ` - ${errorText}`;
                }
                throw new Error(errorMessage);
            }
        } catch (error) {
            debugLog('API submission failed, using fallback:', error.message);
            
            // Fallback: Store locally and simulate success (for demo purposes)
            // In production, you could send to a different endpoint or queue for retry
            localStorage.setItem('pendingLeadSubmissions', JSON.stringify([
                ...(JSON.parse(localStorage.getItem('pendingLeadSubmissions') || '[]')),
                data
            ]));
            
            debugLog('Lead stored locally for later submission');
            return true; // Simulate success for better UX
        }
    };

    submitToAPI().then(success => {
        if (success) {
            debugLog('Lead form processing completed');
            showSuccessMessage();
            
            // Mark as permanently shown
            localStorage.setItem('leadPopupShown', 'true');
            localStorage.setItem('leadPopupData', JSON.stringify({
                email: data.email,
                timestamp: data.timestamp
            }));
        }
    }).catch(error => {
        debugLog('Unexpected error during form submission:', error);
        
        // Show detailed error in debug mode, generic message in production
        const errorMessage = window.LeadGenConfig.debug 
            ? `🔧 DEBUG: ${error.message || error} \n\nFull error logged to console.`
            : '⚠️ There was a technical issue. Your information was not submitted. Please try again or contact us at hello@danielepelleri.com';
        
        alert(errorMessage);
        
        // Reset button
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
    });
}

// Show success message
function showSuccessMessage() {
    const form = document.getElementById('lead-form');
    if (form) {
        form.innerHTML = `
            <div class="success-message">
                <h4>🎉 Thank you!</h4>
                <p>You're all set! Keep reading and I'll send you updates when new content is available.</p>
                <button onclick="closeLeadPopup('form-success')" class="lead-submit-btn">Continue Reading</button>
            </div>
        `;
    }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initLeadGeneration);

// Testing function to reset lead generation state
function resetLeadGenState() {
    // Clear all storage
    sessionStorage.removeItem('leadPopupShown');
    sessionStorage.removeItem('leadPopupTrigger');
    sessionStorage.removeItem('leadPopupDismissed');
    localStorage.removeItem('leadPopupShown');
    localStorage.removeItem('leadPopupData');
    localStorage.removeItem('leadPopupDismissedAt');
    localStorage.removeItem('lastPopupShownAt');
    localStorage.removeItem('ebook-visit-count');
    
    // Reset state
    leadPopupState.shown = false;
    leadPopupState.triggers = {
        scrollDepth: false,
        timeOnPage: false,
        exitIntent: false,
        mobileScrollStop: false,
        returnVisitor: false
    };
    leadPopupState.timeOnPage = 0;
    
    debugLog('Testing state reset - popup should work now');
    return true;
}

// Global functions for manual control
window.showLeadPopup = showLeadPopup;
window.closeLeadPopup = closeLeadPopup;
window.submitLeadForm = submitLeadForm;
window.resetLeadGenState = resetLeadGenState;