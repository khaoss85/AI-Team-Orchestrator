# Piano di Pulizia Repository

## 🗑️ File da Rimuovere Immediatamente

### File di Log Grandi (>100MB)
- `backend/server.log` (126.31 MB)
- `backend/server_debug2.log` (307.39 MB)

### Tutti i File di Log (.log)
```bash
# Rimuovi tutti i file .log dalla root e backend
find . -name "*.log" -delete
```

### Script SQL Temporanei
- `fix_memory_patterns_schema.sql`
- `fix_deliverables_schema.sql`
- `fix_deliverables_schema_complete.sql`
- `orchestration_flows_schema.sql`
- `complete_schema_fix.sql`

### File di Test Sparsi
- `quick_compliance_test.py`
- `test_tools_and_handoffs.py`
- `test_complete_sdk_implementation.py`
- `test_enhanced_qa_deliverables_flow.py`
- `test_runner_isolated.py`
- `test_monitoring_system.py`
- `force_executor_test.py`
- `test_autonomous_deliverable_trigger.py`
- `test_trace_verification.py`
- `comprehensive_verification_test.py`
- Tutti i file `e2e_autonomous_test_*.log`

## 📁 Riorganizzazione

### Creare Struttura Tests
```
tests/
├── unit/
├── integration/
├── e2e/
├── fixtures/
└── README.md
```

### Spostare File di Test
- Spostare tutti i file `test_*.py` in `tests/`
- Categorizzare per tipo (unit/integration/e2e)

## 🛡️ Aggiornare .gitignore

Aggiungere regole per prevenire futuri problemi:
```
# Logs
*.log
logs/
server*.log
debug*.log

# Temporary SQL files
*_temp.sql
temp_*.sql
fix_*.sql

# Test artifacts
test_results/
coverage/
.pytest_cache/

# Temporary files
*.tmp
*.bak
*.swp
*~
```

## 🔧 Comandi di Pulizia

### 1. Rimuovere file grandi da Git history
```bash
git filter-branch --force --index-filter \
'git rm --cached --ignore-unmatch backend/server.log backend/server_debug2.log' \
--prune-empty --tag-name-filter cat -- --all
```

### 2. Rimuovere tutti i log files
```bash
git rm --cached *.log
git rm --cached backend/*.log
```

### 3. Force push per pulire remote
```bash
git push origin --force --all
```