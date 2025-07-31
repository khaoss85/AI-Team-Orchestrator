# Sistema di Monitoraggio Preventivo

## 🎯 Panoramica

Questo sistema di monitoraggio preventivo è stato implementato per evitare problemi futuri con i deliverable e garantire che il sistema funzioni sempre correttamente.

## 🏥 Componenti Installati

### 1. Health Monitor (`health_monitor.py`)
- **Frequenza**: Ogni 5 minuti (automatico)
- **Funzioni**:
  - Rileva workspace in stato "error" e li ripara automaticamente
  - Riavvia l'executor se non è attivo
  - Identifica task "Final Deliverable" bloccati (>30 min)
  - Monitora pipeline di creazione deliverable
  - Genera health score (0-100)

### 2. Sistema di Alert (`alert_system.py`)
- **Email**: Invia notifiche per problemi critici
- **Slack**: Integrazione webhook (opzionale)
- **Rate Limiting**: Evita spam di alert
- **Escalation**: Alert diversi per severità (critical/warning/info)

### 3. Auto-Start Integrato (`main.py`)
- Health monitor si avvia automaticamente con l'applicazione
- Controllo ogni 5 minuti in background
- Logging completo delle attività

### 4. Cron Jobs
- **Health Check**: `*/5 * * * *` (ogni 5 minuti)
- **Daily Report**: `0 9 * * *` (alle 9:00 ogni giorno)
- **Log Cleanup**: `0 2 * * 0` (domenica alle 2:00)

## 🚀 Setup Rapido

### Installazione Automatica
```bash
cd backend
chmod +x setup_monitoring.sh
./setup_monitoring.sh
```

### Configurazione Email/Slack Alert
1. Copia le configurazioni di esempio:
```bash
cp .env.monitoring .env
# oppure aggiungi a .env esistente
```

2. Configura le variabili:
```bash
# Email (Gmail esempio)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
ALERT_EMAIL_USER=your-email@gmail.com
ALERT_EMAIL_PASSWORD=your-app-password
ALERT_RECIPIENTS=admin@company.com,dev@company.com

# Slack (opzionale)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
```

3. Riavvia l'applicazione:
```bash
python3 main.py
```

## 📊 Utilizzo

### Test Manuale
```bash
# Health check semplice
python3 health_monitor.py

# Report dettagliato
python3 health_monitor.py --report
```

### Monitoraggio Log
```bash
# Log health monitor
tail -f logs/health_monitor.log

# Report giornalieri
tail -f logs/daily_reports.log

# Log applicazione principale
tail -f health_monitor.log
```

### Controllo Cron Jobs
```bash
# Vedere cron jobs installati
crontab -l

# Backup cron jobs (creato automaticamente)
ls crontab_backup_*.txt
```

## 🔧 Meccanismi di Auto-Riparazione

### 1. Workspace Error Fix
- **Problema**: Workspace in stato "error"
- **Fix**: Automaticamente cambiato a "active"
- **Alert**: Email/Slack quando applicato

### 2. Executor Restart
- **Problema**: Task executor non attivo
- **Fix**: Riavvio automatico dell'executor
- **Alert**: Notifica dell'azione eseguita

### 3. Stalled Task Detection
- **Problema**: Task "Final Deliverable" bloccati (>30 min)
- **Detection**: Identifica e segnala
- **Future**: Auto-retry da implementare

### 4. Pipeline Health
- **Monitoraggio**: Task completati senza deliverable
- **Threshold**: Alert se >10 task senza deliverable
- **Prevention**: Early detection di problemi

## 📈 Health Score

### Calcolo
- **Base**: 100 punti
- **Problemi**: -15 punti per issue
- **Warning**: -5 punti per warning
- **Fix Applicati**: +5 punti (max +20)

### Soglie
- **90-100**: 🎉 EXCELLENT
- **70-89**: ✅ GOOD  
- **50-69**: ⚠️ NEEDS ATTENTION
- **0-49**: 🚨 CRITICAL

## 🚨 Tipi di Alert

### Critical (Score <30)
- **Trigger**: Health score molto basso
- **Action**: Email immediata + Slack
- **Cooldown**: 60 minuti (configurabile)

### Warning (Score <70 + Issues)
- **Trigger**: Problemi multipli rilevati
- **Action**: Email + Slack
- **Frequency**: Ogni occorrenza

### Info (Auto-fixes)
- **Trigger**: Fix automatici applicati
- **Action**: Notifica informativa
- **Purpose**: Trasparenza delle azioni

## 📂 Struttura File

```
backend/
├── health_monitor.py          # Monitor principale
├── alert_system.py           # Sistema alert
├── setup_monitoring.sh       # Script setup
├── run_health_check.sh       # Wrapper cron
├── run_daily_report.sh       # Report giornaliero  
├── .env.monitoring           # Template config
├── logs/                     # Directory log
│   ├── health_monitor.log    # Log monitor
│   └── daily_reports.log     # Report giornalieri
└── crontab_backup_*.txt      # Backup cron
```

## 🔄 Prevenzione Problemi Futuri

### Problemi Risolti Automaticamente
1. ✅ Workspace in error state
2. ✅ Executor non attivo
3. ✅ Task bloccati (detection)
4. ✅ Pipeline deliverable stoppata

### Problemi Prevenuti
1. ✅ Frontend senza deliverable (early detection)
2. ✅ Task accumulo senza esecuzione
3. ✅ Problemi sistemici non rilevati
4. ✅ Degradazione performance silenziosa

### Benefici a Lungo Termine
- **Uptime**: Sistema sempre operativo
- **Reliability**: Auto-riparazione problemi comuni
- **Transparency**: Visibilità completa su salute sistema
- **Maintenance**: Manutenzione predittiva invece di reattiva

## 🛠️ Troubleshooting

### Health Monitor Non Funziona
```bash
# Controlla se è in esecuzione
ps aux | grep health_monitor

# Controlla log per errori
tail -f logs/health_monitor.log

# Test manuale
python3 health_monitor.py --report
```

### Alert Non Arrivano
1. Controlla configurazione email in `.env`
2. Verifica credenziali SMTP
3. Controlla firewall/rete per SMTP
4. Test webhook Slack se configurato

### Cron Jobs Non Attivi
```bash
# Controlla se cron service è attivo
sudo service cron status

# Verifica cron jobs
crontab -l

# Controlla log cron
sudo tail -f /var/log/cron
```

## 📞 Supporto

Per problemi o miglioramenti:
1. Controlla log in `logs/`
2. Esegui test manuale con `--report`
3. Verifica configurazione `.env`
4. Controlla health score e alert ricevuti

Il sistema è progettato per essere **self-healing** e richiedere intervento manuale minimo.