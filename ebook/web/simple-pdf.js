#!/usr/bin/env node

const puppeteer = require('puppeteer');
const fs = require('fs');

/**
 * Simple PDF Generator for AI Team Orchestrator
 * Handles large HTML files with memory optimization
 */

async function generateSimplePDF(language = 'en') {
  console.log(`🚀 Generating simple PDF for ${language.toUpperCase()}...`);
  
  const browser = await puppeteer.launch({
    headless: 'new',
    args: [
      '--no-sandbox', 
      '--disable-setuid-sandbox',
      '--disable-web-security',
      '--disable-features=VizDisplayCompositor',
      '--max_old_space_size=4096'
    ]
  });

  try {
    const page = await browser.newPage();
    
    // Increase memory limits
    await page.setDefaultNavigationTimeout(120000);
    await page.setDefaultTimeout(120000);
    
    const bookUrl = `http://localhost:8888/${language}/book.html`;
    console.log(`📖 Loading: ${bookUrl}`);
    
    await page.goto(bookUrl, { 
      waitUntil: 'domcontentloaded',
      timeout: 120000 
    });
    
    // Wait for basic content
    await page.waitForTimeout(5000);
    
    // Simple print CSS
    await page.addStyleTag({
      content: `
        @media print {
          * { -webkit-print-color-adjust: exact !important; color-adjust: exact !important; }
          body { margin: 0; padding: 20px; }
          .reader-tools, nav, .breadcrumb, .no-print { display: none !important; }
          .chapter { page-break-before: auto; margin: 20px 0; }
          h1, h2 { page-break-after: avoid; }
          pre, code { font-size: 12px; }
        }
      `
    });
    
    const filename = `AI-Team-Orchestrator-${language.toUpperCase()}-Simple.pdf`;
    
    console.log(`📄 Generating PDF: ${filename}`);
    
    // Simplified PDF options
    await page.pdf({
      path: filename,
      format: 'A4',
      printBackground: true,
      margin: { top: '20mm', bottom: '20mm', left: '20mm', right: '20mm' },
      timeout: 300000, // 5 minutes
      preferCSSPageSize: false
    });
    
    console.log(`✅ PDF generated: ${filename}`);
    
    const stats = fs.statSync(filename);
    const fileSizeInMB = (stats.size / (1024*1024)).toFixed(2);
    console.log(`📊 File size: ${fileSizeInMB} MB`);
    
    return filename;
    
  } catch (error) {
    console.error('❌ Error:', error.message);
    throw error;
  } finally {
    await browser.close();
  }
}

// Execute
if (require.main === module) {
  const language = process.argv[2] || 'en';
  
  generateSimplePDF(language)
    .then(filename => {
      console.log(`\n🎉 SUCCESS! PDF: ${filename}`);
    })
    .catch(error => {
      console.error('\n💥 FAILED:', error.message);
      process.exit(1);
    });
}

module.exports = { generateSimplePDF };