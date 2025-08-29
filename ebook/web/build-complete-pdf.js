#!/usr/bin/env node

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

/**
 * AI Team Orchestrator - Complete PDF Builder
 * Combines all chapters into a professional PDF ebook
 */

// Chapter order definition
const CHAPTERS_EN = [
  // Cover and intro
  { title: 'AI Team Orchestrator', url: '/en/ai-team-orchestrator.html', isIntro: true },
  
  // Movement 1: Core Philosophy & Architecture
  { title: 'Movement 1: Core Philosophy & Architecture', url: '/en/core-philosophy-architecture/', isSection: true },
  { title: 'Preface: The Map for the Hidden Iceberg', url: '/en/core-philosophy-architecture/preface/' },
  { title: 'The 15 Pillars of AI Systems', url: '/en/core-philosophy-architecture/15-pillars-ai-system/' },
  { title: 'First Specialist Agent Architecture', url: '/en/core-philosophy-architecture/first-specialist-agent-architecture/' },
  { title: 'AI Mocking & Testing Strategy', url: '/en/core-philosophy-architecture/ai-mocking-testing-strategy/' },
  { title: 'SDK vs Direct API Battle', url: '/en/core-philosophy-architecture/sdk-vs-direct-api-battle/' },
  { title: 'Agent Toolbox & Tools Registry', url: '/en/core-philosophy-architecture/agent-toolbox/' },
  { title: 'Failed Handoff & Delegation', url: '/en/core-philosophy-architecture/failed-handoff-delegation/' },
  { title: 'Tool Testing: Reality Anchor', url: '/en/core-philosophy-architecture/tool-testing-reality-anchor/' },
  { title: 'Orchestrator as Conductor', url: '/en/core-philosophy-architecture/orchestrator-conductor/' },
  { title: 'AI Recruiter for Dynamic Teams', url: '/en/core-philosophy-architecture/ai-recruiter-dynamic-team/' },
  { title: 'Agent-Environment Interactions', url: '/en/core-philosophy-architecture/agent-environment-interactions/' },
  { title: 'Drama: Parsing AI Contracts', url: '/en/core-philosophy-architecture/drama-parsing-ai-contracts/' },
  
  // Movement 2: Execution & Quality
  { title: 'Movement 2: Execution & Quality', url: '/en/execution-quality/', isSection: true },
  { title: 'Quality Gates & Human-in-the-Loop', url: '/en/execution-quality/quality-gates-human-loop/' },
  { title: 'Memory System: The Agent Learns', url: '/en/execution-quality/memory-system-learning/' },
  { title: 'Improvement Cycle & Auto-Correction', url: '/en/execution-quality/improvement-cycle-correction/' },
  { title: 'Comprehensive Test: The Maturity Exam', url: '/en/execution-quality/comprehensive-test/' },
  { title: 'Consolidation Test: Simplify to Survive', url: '/en/execution-quality/consolidation-test/' },
  { title: 'Production Test: Real World Survival', url: '/en/execution-quality/production-test/' },
  { title: 'Autonomous Monitoring & Control', url: '/en/execution-quality/autonomous-monitoring/' },
  { title: 'Final Assembly: The Last Mile', url: '/en/execution-quality/final-assembly-last-mile/' },
  
  // Movement 3: User Experience & Transparency
  { title: 'Movement 3: User Experience & Transparency', url: '/en/user-experience-transparency/', isSection: true },
  { title: 'Onboarding UX: User Experience', url: '/en/user-experience-transparency/onboarding-ux/' },
  { title: 'AI Team Org Chart: Who Does What', url: '/en/user-experience-transparency/ai-team-org-chart/' },
  { title: 'Contextual Chat: Dialog with AI Team', url: '/en/user-experience-transparency/contextual-chat/' },
  { title: 'Control Room: Monitoring & Telemetry', url: '/en/user-experience-transparency/control-room/' },
  { title: 'QA Chain of Thought: The Architectural Fork', url: '/en/user-experience-transparency/qa-chain-of-thought/' },
  { title: 'Deep Reasoning: The Black Box', url: '/en/user-experience-transparency/deep-reasoning/' },
  { title: 'B2B SaaS Thesis: Prove Versatility', url: '/en/user-experience-transparency/b2b-saas-thesis/' },
  { title: 'Fitness Antithesis: Challenge Limits', url: '/en/user-experience-transparency/fitness-antithesis/' },
  { title: 'Synthesis: Functional Abstraction', url: '/en/user-experience-transparency/synthesis-abstraction/' },
  { title: 'The Strategist Agent: Next Frontier', url: '/en/user-experience-transparency/strategist-agent/' },
  { title: 'Tech Stack: The Foundations', url: '/en/user-experience-transparency/tech-stack/' },
  { title: 'Conclusion: A Team, Not a Tool', url: '/en/user-experience-transparency/team-not-tool/' },
  
  // Movement 4: Memory System & Scaling  
  { title: 'Movement 4: Memory System & Scaling', url: '/en/memory-system-scaling/', isSection: true },
  { title: 'The Great Refactoring: Universal Pipeline', url: '/en/memory-system-scaling/great-refactoring/' },
  { title: 'Load Testing Shock: Success is the Enemy', url: '/en/memory-system-scaling/load-testing-shock/' },
  { title: 'Rate Limiting & Circuit Breakers: Resilience', url: '/en/memory-system-scaling/rate-limiting-resilience/' },
  { title: 'Semantic Caching System: Optimization', url: '/en/memory-system-scaling/semantic-caching/' },
  { title: 'Service Registry: Architecture Ecosystem', url: '/en/memory-system-scaling/service-registry/' },
  { title: 'Holistic Memory Consolidation: Unification', url: '/en/memory-system-scaling/memory-consolidation/' },
  { title: 'Orchestrator Wars: The Unified', url: '/en/memory-system-scaling/orchestrator-wars/' },
  { title: 'Global Scale Architecture: Timezone', url: '/en/memory-system-scaling/global-scale/' },
  { title: 'Production Readiness Audit: Moment of Truth', url: '/en/memory-system-scaling/production-readiness-audit/' },
  { title: 'Enterprise Security Hardening: Paranoia', url: '/en/memory-system-scaling/security-hardening/' },
  { title: 'Epilogue: From MVP to Global Platform - The Journey', url: '/en/memory-system-scaling/epilogue-journey/' }
];

async function buildCompletePDF(language = 'en', maxPages = null) {
  console.log(`🚀 Building complete PDF for ${language.toUpperCase()}...`);
  
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-web-security']
  });

  let allHTML = `
    <!DOCTYPE html>
    <html lang="${language}">
    <head>
      <meta charset="UTF-8">
      <title>AI Team Orchestrator - Complete Guide</title>
      <style>
        body { 
          font-family: Georgia, 'Times New Roman', serif; 
          line-height: 1.6; 
          margin: 0; 
          padding: 20px;
          color: #2c3e50;
        }
        
        .cover-page {
          text-align: center;
          page-break-after: always;
          padding: 100px 20px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          min-height: 80vh;
          display: flex;
          flex-direction: column;
          justify-content: center;
        }
        
        .cover-page h1 {
          font-size: 3em;
          margin-bottom: 0.5em;
          text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .cover-page h2 {
          font-size: 1.5em;
          margin-bottom: 2em;
          opacity: 0.9;
        }
        
        .section-title {
          page-break-before: always;
          text-align: center;
          padding: 80px 20px;
          background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
          margin: 40px -20px;
        }
        
        .section-title h1 {
          font-size: 2.5em;
          color: #2c3e50;
          margin: 0;
        }
        
        .chapter {
          page-break-before: always;
          margin: 40px 0;
        }
        
        .chapter h1 {
          color: #2c3e50;
          border-bottom: 3px solid #3498db;
          padding-bottom: 10px;
          font-size: 2em;
        }
        
        .war-story {
          border-left: 5px solid #e74c3c;
          background: #fdf2f2;
          padding: 20px;
          margin: 20px 0;
          page-break-inside: avoid;
        }
        
        .key-takeaways {
          border-left: 5px solid #27ae60;
          background: #f1f8e9;
          padding: 20px;
          margin: 20px 0;
          page-break-inside: avoid;
        }
        
        .mermaid {
          text-align: center;
          margin: 20px 0;
          page-break-inside: avoid;
        }
        
        pre, code {
          font-family: 'Courier New', monospace;
          background: #f8f9fa;
          padding: 10px;
          border-radius: 5px;
          font-size: 12px;
          page-break-inside: avoid;
        }
        
        h1, h2, h3 { page-break-after: avoid; }
        
        @page {
          margin: 20mm;
          @top-center { content: "AI Team Orchestrator - Daniele Pelleri"; }
          @bottom-center { content: counter(page); }
        }
        
        @media print {
          .no-print, .reader-tools, nav, .breadcrumb { display: none !important; }
          * { -webkit-print-color-adjust: exact !important; color-adjust: exact !important; }
        }
      </style>
    </head>
    <body>
      <!-- Cover Page -->
      <div class="cover-page">
        <h1>🤖 AI Team Orchestrator</h1>
        <h2>From MVP to Global Platform</h2>
        <p style="font-size: 1.2em;">The Complete Journey</p>
        <p style="margin-top: 60px; font-size: 1.1em;">by Daniele Pelleri</p>
        <p style="font-style: italic; margin-top: 40px;">42 practical chapters to build AI systems that self-orchestrate and scale globally</p>
      </div>
  `;

  try {
    const page = await browser.newPage();
    let processedChapters = 0;
    
    for (const chapter of CHAPTERS_EN) {
      if (maxPages && processedChapters >= maxPages) break;
      
      try {
        if (chapter.isSection) {
          // Add section divider
          allHTML += `
            <div class="section-title">
              <h1>${chapter.title}</h1>
            </div>
          `;
          console.log(`📑 Added section: ${chapter.title}`);
        } else {
          console.log(`📖 Processing: ${chapter.title}...`);
          
          const fullUrl = `http://localhost:8888${chapter.url}`;
          await page.goto(fullUrl, { 
            waitUntil: 'domcontentloaded',
            timeout: 30000 
          });
          
          // Extract main content
          const content = await page.evaluate(() => {
            // Remove navigation and tools
            const elementsToRemove = document.querySelectorAll('.reader-tools, nav, .breadcrumb, .no-print, footer, .continue-reading-section');
            elementsToRemove.forEach(el => el.remove());
            
            // Get main content
            const container = document.querySelector('.container, main, .chapter-content, body');
            return container ? container.innerHTML : document.body.innerHTML;
          });
          
          allHTML += `
            <div class="chapter">
              <h1>${chapter.title}</h1>
              ${content}
            </div>
          `;
          
          processedChapters++;
        }
      } catch (error) {
        console.warn(`⚠️  Skipped ${chapter.title}: ${error.message}`);
      }
      
      // Small delay to prevent overwhelming
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    allHTML += '</body></html>';
    
    // Generate PDF from combined HTML
    console.log(`📄 Generating final PDF with ${processedChapters} chapters...`);
    
    await page.setContent(allHTML, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2000);
    
    const timestamp = new Date().toISOString().split('T')[0];
    const filename = `AI-Team-Orchestrator-Complete-${language.toUpperCase()}-${timestamp}.pdf`;
    
    await page.pdf({
      path: filename,
      format: 'A4',
      printBackground: true,
      margin: { top: '15mm', bottom: '15mm', left: '15mm', right: '15mm' },
      timeout: 180000
    });
    
    console.log(`✅ Complete PDF generated: ${filename}`);
    
    const stats = fs.statSync(filename);
    const fileSizeInMB = (stats.size / (1024*1024)).toFixed(2);
    console.log(`📊 File size: ${fileSizeInMB} MB`);
    console.log(`📚 Chapters included: ${processedChapters}`);
    
    return filename;
    
  } catch (error) {
    console.error('❌ Error building PDF:', error);
    throw error;
  } finally {
    await browser.close();
  }
}

// Execute
if (require.main === module) {
  const language = process.argv[2] || 'en';
  const maxPages = process.argv[3] ? parseInt(process.argv[3]) : null;
  
  buildCompletePDF(language, maxPages)
    .then(filename => {
      console.log(`\n🎉 SUCCESS! Complete PDF: ${filename}`);
      console.log(`\n📋 Next steps:`);
      console.log(`   1. Review the PDF quality`);
      console.log(`   2. Add download link to website`);
      console.log(`   3. Generate Italian version: node build-complete-pdf.js it`);
    })
    .catch(error => {
      console.error('\n💥 FAILED:', error.message);
      process.exit(1);
    });
}

module.exports = { buildCompletePDF };