// Performance Test Script
// Run this in browser console to measure conversation interface load times

console.log('🚀 Performance Test: Conversation Interface Load Times');
console.log('======================================================');

const startTime = performance.now();
let loadingPhases = {};

// Monitor for various loading phases
const observer = new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    if (entry.name.includes('conversation')) {
      console.log(`📊 ${entry.name}: ${entry.duration.toFixed(2)}ms`);
    }
  }
});

observer.observe({ entryTypes: ['navigation', 'measure'] });

// Monitor network requests
const originalFetch = window.fetch;
window.fetch = function(...args) {
  const url = args[0];
  const startTime = performance.now();
  
  return originalFetch.apply(this, args).then(response => {
    const endTime = performance.now();
    const duration = endTime - startTime;
    
    if (url.includes('unified-assets')) {
      console.log(`🚨 SLOW UNIFIED ASSETS: ${url} - ${duration.toFixed(2)}ms`);
    } else if (url.includes('goals')) {
      console.log(`📊 GOALS API: ${url} - ${duration.toFixed(2)}ms`);
    } else if (url.includes('workspace')) {
      console.log(`⚡ WORKSPACE API: ${url} - ${duration.toFixed(2)}ms`);
    }
    
    return response;
  });
};

// Track React component render times
window.addEventListener('load', () => {
  const endTime = performance.now();
  const totalTime = endTime - startTime;
  
  console.log(`\n✅ CONVERSATION INTERFACE LOADED`);
  console.log(`📊 Total Load Time: ${totalTime.toFixed(2)}ms`);
  
  if (totalTime < 5000) {
    console.log(`🎉 PERFORMANCE EXCELLENT: Under 5 seconds!`);
  } else if (totalTime < 10000) {
    console.log(`✅ PERFORMANCE GOOD: Under 10 seconds`);
  } else {
    console.log(`⚠️  PERFORMANCE SLOW: Over 10 seconds`);
  }
});

// Test progressive loading
setTimeout(() => {
  console.log('\n🔄 Progressive Loading Status Check:');
  
  // Check if basic UI is loaded
  const chatSidebar = document.querySelector('[data-testid="chat-sidebar"]') || 
                     document.querySelector('.chat-sidebar') ||
                     document.querySelector('[class*="sidebar"]');
  
  const messageArea = document.querySelector('[data-testid="messages"]') || 
                     document.querySelector('.messages') ||
                     document.querySelector('[class*="message"]');
                     
  console.log(`📱 Chat Sidebar Loaded: ${chatSidebar ? '✅' : '❌'}`);
  console.log(`💬 Message Area Loaded: ${messageArea ? '✅' : '❌'}`);
  
  if (chatSidebar && messageArea) {
    console.log('🎉 BASIC CONVERSATION UI READY FOR INTERACTION');
  }
}, 2000);

// Monitor for heavy asset loading
setTimeout(() => {
  console.log('\n📦 Heavy Assets Loading Check:');
  console.log('(Goals and unified assets should load progressively in background)');
}, 5000);