#!/bin/bash

# 📚 AI Team Orchestrator - PDF Build Script
# Genera PDF ottimizzato per distribuzione commerciale

echo "🚀 Avvio generazione PDF per AI Team Orchestrator..."

# Verifica Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js non trovato. Installa Node.js 16+ per continuare."
    exit 1
fi

# Verifica file HTML
if [ ! -f "AI_Team_Orchestrator_Libro_FINALE.html" ]; then
    echo "❌ File libro non trovato. Assicurati di essere nella directory web/"
    exit 1
fi

# Installa dipendenze se necessario
if [ ! -d "node_modules" ]; then
    echo "📦 Installazione dipendenze..."
    npm install
fi

# Genera PDF
echo "📄 Generazione PDF in corso..."
node convert_to_pdf.js

# Verifica risultato
if [ -f "AI_Team_Orchestrator_Libro_FINALE.pdf" ]; then
    echo "✅ PDF generato con successo!"
    
    # Mostra info file
    size=$(du -h "AI_Team_Orchestrator_Libro_FINALE.pdf" | cut -f1)
    echo "📊 Dimensione file: $size"
    
    # Suggerimenti per distribuzione
    echo ""
    echo "🎯 Il tuo PDF è pronto per:"
    echo "   📚 Amazon Kindle Direct Publishing (KDP)"
    echo "   💰 Distribuzione commerciale (€40)"
    echo "   🏢 Licensing aziendale"
    echo "   📧 Direct sales"
    echo ""
    echo "📁 File generato: AI_Team_Orchestrator_Libro_FINALE.pdf"
else
    echo "❌ Errore durante la generazione PDF"
    exit 1
fi