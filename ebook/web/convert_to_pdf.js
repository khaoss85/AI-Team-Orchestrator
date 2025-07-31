#!/usr/bin/env node

/**
 * 📚 AI Team Orchestrator - PDF Converter
 * Converte il libro web in PDF di alta qualità mantenendo layout e styling
 * 
 * Uso: node convert_to_pdf.js
 * Output: AI_Team_Orchestrator_Libro_FINALE.pdf
 */

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

async function convertToPDF() {
    console.log('🚀 Avvio conversione PDF...');
    
    const browser = await puppeteer.launch({
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    const page = await browser.newPage();
    
    // Imposta viewport per desktop
    await page.setViewport({ width: 1200, height: 800 });
    
    // Carica il libro
    const htmlPath = path.resolve(__dirname, 'AI_Team_Orchestrator_Libro_FINALE.html');
    const fileUrl = `file://${htmlPath}`;
    
    console.log('📖 Caricamento libro...');
    await page.goto(fileUrl, { 
        waitUntil: 'networkidle0',
        timeout: 60000 
    });
    
    // Attendi che Mermaid carichi tutti i diagrammi
    console.log('🎨 Rendering diagrammi Mermaid...');
    await page.waitForTimeout(5000);
    
    // Verifica che Mermaid abbia completato il rendering
    await page.evaluate(() => {
        return new Promise((resolve) => {
            if (typeof mermaid !== 'undefined') {
                mermaid.initialize({ 
                    startOnLoad: true,
                    theme: 'default',
                    flowchart: { useMaxWidth: true }
                });
                setTimeout(resolve, 3000);
            } else {
                resolve();
            }
        });
    });
    
    // Aggiungi CSS specifico per PDF
    await page.addStyleTag({
        content: `
            /* CSS Ottimizzazioni PDF */
            @media print {
                body {
                    -webkit-print-color-adjust: exact !important;
                    color-adjust: exact !important;
                    print-color-adjust: exact !important;
                }
                
                .book-container {
                    box-shadow: none;
                    margin: 0;
                    background: white;
                }
                
                /* Gestione page breaks */
                .chapter {
                    page-break-before: always;
                    break-before: page;
                }
                
                .chapter:first-child {
                    page-break-before: avoid;
                    break-before: avoid;
                }
                
                /* Mantieni insieme sezioni importanti */
                .key-takeaways-section,
                .war-story,
                .architecture-section {
                    page-break-inside: avoid;
                    break-inside: avoid;
                }
                
                /* Ottimizza tabelle per print */
                table {
                    page-break-inside: auto;
                    break-inside: auto;
                }
                
                tr {
                    page-break-inside: avoid;
                    break-inside: avoid;
                }
                
                /* Nascondi elementi interattivi */
                .floating-toc,
                .toc-toggle,
                .copy-button,
                .chapter-navigation {
                    display: none !important;
                }
                
                /* Migliora contrasto per print */
                .mermaid svg {
                    background: white;
                }
                
                /* Assicura font leggibili */
                body, p, td, th, li {
                    font-size: 11pt !important;
                    line-height: 1.4 !important;
                }
                
                h1 { font-size: 18pt !important; }
                h2 { font-size: 16pt !important; }
                h3 { font-size: 14pt !important; }
                h4 { font-size: 12pt !important; }
                
                code {
                    font-size: 9pt !important;
                    background: #f5f5f5 !important;
                    border: 1px solid #ddd !important;
                }
                
                pre code {
                    font-size: 8pt !important;
                }
            }
        `
    });
    
    console.log('📄 Generazione PDF...');
    
    const pdf = await page.pdf({
        path: 'AI_Team_Orchestrator_Libro_FINALE.pdf',
        format: 'A4',
        margin: {
            top: '0.8in',
            bottom: '0.8in', 
            left: '0.7in',
            right: '0.7in'
        },
        printBackground: true,
        displayHeaderFooter: true,
        headerTemplate: `
            <div style="font-size: 10px; margin: 0 auto; color: #666; text-align: center; width: 100%;">
                AI Team Orchestrator - Da MVP a Global Platform
            </div>
        `,
        footerTemplate: `
            <div style="font-size: 10px; margin: 0 auto; color: #666; text-align: center; width: 100%;">
                <span>© 2025 Daniele Pelleri - Pagina <span class="pageNumber"></span> di <span class="totalPages"></span></span>
            </div>
        `,
        preferCSSPageSize: false,
        timeout: 120000
    });
    
    await browser.close();
    
    const stats = fs.statSync('AI_Team_Orchestrator_Libro_FINALE.pdf');
    const fileSizeMB = (stats.size / 1024 / 1024).toFixed(2);
    
    console.log('✅ PDF generato con successo!');
    console.log(`📊 Dimensione: ${fileSizeMB} MB`);
    console.log(`📁 File: AI_Team_Orchestrator_Libro_FINALE.pdf`);
    console.log('🎯 Pronto per Amazon KDP e distribuzione commerciale!');
}

// Gestione errori
convertToPDF().catch(error => {
    console.error('❌ Errore durante la conversione:', error);
    process.exit(1);
});