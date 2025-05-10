# AI Team Orchestrator

Una piattaforma SaaS che ti consente di "ingaggiare" un vero e proprio team di agenti AI
e lasciarli lavorare in completa autonomia su un progetto.

## Funzionalità Principali

- **Direttore Virtuale**: Analizza i progetti, propone team di agenti specializzati e gestisce l'avanzamento
- **Agenti Specialisti**: Ognuno con ruolo e seniority specifici, capaci di collaborare autonomamente
- **Handoff Intelligenti**: Passaggio automatico di task tra agenti quando necessario
- **Monitoraggio in tempo reale**: Tracciamento dello stato di salute e dell'avanzamento degli agenti

## Tecnologie Utilizzate

- **Frontend**: Next.js (App Router) con TailwindCSS
- **Backend**: FastAPI in Python
- **Database**: Supabase
- **AI**: OpenAI Agents SDK

## Prerequisiti

- Node.js 18+
- Python 3.11+
- Docker e Docker Compose (opzionale, per il deployment)
- Chiave API OpenAI
- Account Supabase

## Installazione e Sviluppo

### Configurazione Ambiente

1. Clona il repository:
   ```bash
   git clone https://github.com/tuonome/ai-team-orchestrator.git
   cd ai-team-orchestrator