#!/usr/bin/env node

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

/**
 * AI Team Orchestrator PDF Generator
 * Converts the complete HTML book to a professional PDF ebook
 */

async function generatePDF(language = 'en', outputDir = './pdfs') {
  console.log(`🚀 Generating PDF for ${language.toUpperCase()} version...`);
  
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  try {
    const page = await browser.newPage();
    
    // Set viewport for consistent rendering
    await page.setViewport({ width: 1200, height: 1600 });
    
    // Load the complete book
    const bookUrl = `http://localhost:8888/${language}/book.html`;
    console.log(`📖 Loading: ${bookUrl}`);
    
    await page.goto(bookUrl, { 
      waitUntil: 'networkidle2',
      timeout: 60000 
    });
    
    // Wait for any dynamic content to load
    await page.waitForTimeout(3000);
    
    // Add print-specific CSS
    await page.addStyleTag({
      content: `
        /* PDF Print Optimizations */
        @media print {
          .no-print, .reader-tools, nav, .breadcrumb { display: none !important; }
          .chapter { page-break-before: always; }
          body { -webkit-print-color-adjust: exact; color-adjust: exact; }
          .mermaid svg { max-width: 100% !important; height: auto !important; }
          pre, code { page-break-inside: avoid; }
          .war-story, .key-takeaways { page-break-inside: avoid; }
          h1, h2, h3 { page-break-after: avoid; }
        }
        
        /* Consistent typography for PDF */
        body { font-family: 'Georgia', 'Times New Roman', serif; }
        code, pre { font-family: 'Courier New', monospace; }
        
        /* Enhanced contrast for print */
        .war-story { border: 2px solid #e74c3c; background: #fdf2f2 !important; }
        .key-takeaways { border: 2px solid #27ae60; background: #f1f8e9 !important; }
      `
    });
    
    // Create output directory
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }
    
    // Generate PDF with optimized settings
    const timestamp = new Date().toISOString().split('T')[0];
    const filename = `AI-Team-Orchestrator-${language.toUpperCase()}-${timestamp}.pdf`;
    const outputPath = path.join(outputDir, filename);
    
    console.log(`📄 Generating PDF: ${filename}`);
    
    const pdf = await page.pdf({
      path: outputPath,
      format: 'A4',
      printBackground: true,
      displayHeaderFooter: true,
      headerTemplate: `
        <div style="font-size: 10px; text-align: center; width: 100%; margin-top: 10px; color: #666;">
          <span style="font-weight: bold;">AI Team Orchestrator</span> - From MVP to Global Platform
        </div>
      `,
      footerTemplate: `
        <div style="font-size: 10px; text-align: center; width: 100%; margin-bottom: 10px; color: #666;">
          <span style="margin-left: 48%;">Page <span class="pageNumber"></span> of <span class="totalPages"></span></span>
        </div>
      `,
      margin: { 
        top: '1.5cm', 
        bottom: '1.5cm', 
        left: '2cm', 
        right: '2cm' 
      },
      preferCSSPageSize: false,
      timeout: 120000
    });
    
    console.log(`✅ PDF generated successfully: ${outputPath}`);
    
    // Get file size
    const stats = fs.statSync(outputPath);
    const fileSizeInMB = (stats.size / (1024*1024)).toFixed(2);
    console.log(`📊 File size: ${fileSizeInMB} MB`);
    
    return outputPath;
    
  } catch (error) {
    console.error('❌ Error generating PDF:', error);
    throw error;
  } finally {
    await browser.close();
  }
}

// CLI execution
if (require.main === module) {
  const language = process.argv[2] || 'en';
  const outputDir = process.argv[3] || './pdfs';
  
  generatePDF(language, outputDir)
    .then(path => {
      console.log(`\n🎉 SUCCESS! PDF available at: ${path}`);
      console.log(`\n📋 Next steps:`);
      console.log(`   1. Review the generated PDF`);
      console.log(`   2. Add download link to website`);
      console.log(`   3. Consider generating Italian version: node generate-pdf.js it`);
    })
    .catch(error => {
      console.error('\n💥 FAILED:', error.message);
      process.exit(1);
    });
}

module.exports = { generatePDF };