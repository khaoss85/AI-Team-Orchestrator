### **Capitolo 9: Il Recruiter AI (`Director`) – La Nascita del Team Dinamico**

**Data:** 26 Luglio

Il nostro sistema stava diventando sofisticato. Avevamo agenti specializzati, un orchestratore intelligente e un meccanismo di collaborazione robusto. Ma c'era ancora un enorme elemento hard-coded nel cuore del sistema: **il team stesso**. Per ogni nuovo progetto, eravamo noi a decidere manually quali ruoli servissero, quanti agenti creare e con quali competenze.

Questo approccio era un collo di bottiglia per la scalabilità e una violazione diretta del nostro **Pilastro #3 (Universale & Language-Agnostic)**. Un sistema che richiede a un umano di configurare il team per ogni nuovo dominio di business non è né universale né veramente autonomo.

La soluzione doveva essere radicale: dovevamo insegnare al sistema a **costruire il proprio team**. Dovevamo creare un **Recruiter AI**.

#### **La Filosofia: Gli Agenti come Colleghi Digitali**

Prima di scrivere il codice, abbiamo definito una filosofia: **i nostri agenti non sono "script", sono "colleghi"**. Volevamo che il nostro sistema di creazione del team rispecchiasse il processo di recruiting di un'organizzazione umana eccellente.

Un recruiter HR non assume basandosi solo su una lista di "hard skills". Valuta la personalità, le soft skills, il potenziale di collaborazione e come la nuova risorsa si integrerà nella cultura del team esistente. Abbiamo deciso che il nostro `Director` AI doveva fare esattamente lo stesso.

Questo significa che ogni agente nel nostro sistema non è definito solo dal suo `role` (es. "Lead Developer"), ma da un profilo completo che include:

*   **Hard Skills:** Le competenze tecniche misurabili (es. "Python", "React", "SQL").
*   **Soft Skills:** Le capacità interpersonali e di ragionamento (es. "Problem Solving", "Comunicazione Strategica").
*   **Personalità:** Tratti che influenzano il suo stile di lavoro (es. "Pragmatico e diretto", "Creativo e collaborativo").
*   **Background Story:** Una breve narrazione che dà contesto e "colore" al suo profilo, rendendolo più comprensibile e intuitivo per l'utente umano.

Questo approccio non è un vezzo stilistico. È una decisione architetturale che ha profonde implicazioni:

1.  **Migliora il Matching Agente-Task:** Un task che richiede "analisi critica" può essere assegnato a un agente con un'alta skill di "Problem Solving", non solo a quello con il ruolo generico di "Analista".
2.  **Aumenta la Trasparenza per l'Utente:** Per l'utente finale, è molto più intuitivo capire perché "Marco Bianchi, il Lead Developer pragmatico" sta lavorando su un task tecnico, piuttosto che vedere un generico "Agente #66f6e770".
3.  **Guida l'AI a Decisioni Migliori:** Fornire all'LLM un profilo così ricco permette al modello di "impersonare" quel ruolo in modo molto più efficace, producendo risultati di qualità superiore.

#### **La Decisione Architetturale: dall'Assegnazione alla Composizione del Team**

Abbiamo creato un nuovo agente di sistema, il `Director`. Il suo ruolo non è eseguire task di business, ma svolgere una funzione meta: **analizzare l'obiettivo di un workspace e proporre la composizione del team ideale per raggiungerlo.**

*Codice di riferimento: `backend/director.py`*

Il processo del `Director` è un vero e proprio ciclo di recruiting AI.

**Flusso di Composizione del Team del `Director`:**

```mermaid
graph TD
    A[Nuovo Workspace Creato] --> B{Analisi Semantica del Goal};
    B --> C{Estrazione Competenze Chiave};
    C --> D{Definizione Ruoli Necessari};
    D --> E{Generazione Profili Agenti Completi};
    E --> F[Proposta del Team];
    F --> G{Approvazione Umana/Automatica};
    G -- Approvato --> H[Creazione Agenti nel DB];

    subgraph "Fase 1: Analisi Strategica (AI)"
        B[Il `Director` legge il goal del workspace]
        C[L'AI identifica le skill necessarie: "email marketing", "data analysis", "copywriting"]
        D[L'AI raggruppa le skill in ruoli: "Marketing Strategist", "Data Analyst"]
    end

    subgraph "Fase 2: Creazione Profili (AI)"
        E[Per ogni ruolo, l'AI genera un profilo completo: nome, seniority, hard/soft skills, background]
    end
    
    subgraph "Fase 3: Finalizzazione"
        F[Il `Director` presenta il team proposto con una giustificazione strategica]
        G[L'utente approva o il sistema auto-approva]
        H[Gli agenti vengono salvati nel database e attivati]
    end
```

#### **Il Cuore del Sistema: Il Prompt del Recruiter AI**

Per realizzare questa visione, il prompt del `Director` doveva essere incredibilmente dettagliato.

*Codice di riferimento: `backend/director.py` (logica `_generate_team_proposal_with_ai`)*
```python
prompt = f"""
Sei un Direttore di un'agenzia di talenti AI di livello mondiale. Il tuo compito è analizzare l'obiettivo di un nuovo progetto e assemblare il team di agenti AI perfetto per garantirne il successo, trattando ogni agente come un professionista umano.

**Obiettivo del Progetto:**
"{workspace_goal}"

**Budget a Disposizione:** {budget} EUR
**Timeline Prevista:** {timeline}

**Analisi Richiesta:**
1.  **Decomposizione Funzionale:** Scomponi l'obiettivo nelle sue principali aree funzionali (es. "Ricerca Dati", "Scrittura Creativa", "Analisi Tecnica", "Gestione Progetto").
2.  **Mappatura Ruoli-Competenze:** Per ogni area funzionale, definisci il ruolo specialistico necessario e le 3-5 competenze chiave (hard skills) indispensabili.
3.  **Definizione Soft Skills:** Per ogni ruolo, identifica 2-3 soft skills cruciali (es. "Problem Solving" per un analista, "Empatia" per un designer).
4.  **Composizione del Team Ottimale:** Assembla un team di 3-5 agenti, bilanciando le competenze per coprire tutte le aree senza sovrapposizioni inutili. Assegna una seniority (Junior, Mid, Senior) a ogni ruolo in base alla complessità.
5.  **Ottimizzazione Budget:** Assicurati che il costo totale stimato del team non superi il budget. Privilegia l'efficienza: un team più piccolo e senior è spesso meglio di uno grande e junior.
6.  **Generazione Profili Completi:** Per ogni agente, crea un nome realistico, una personalità e una breve background story che ne giustifichi le competenze.

**Output Format (JSON only):**
{{
  "team_proposal": [
    {{
      "name": "Nome Agente",
      "role": "Ruolo Specializzato",
      "seniority": "Senior",
      "hard_skills": ["skill 1", "skill 2"],
      "soft_skills": ["skill 1", "skill 2"],
      "personality": "Pragmatico e orientato ai dati.",
      "background_story": "Una breve storia che contestualizza le sue competenze.",
      "estimated_cost_eur": 5000
    }}
  ],
  "total_estimated_cost": 15000,
  "strategic_reasoning": "La logica dietro la composizione di questo team..."
}}
"""
```

#### **"War Story": L'Agente che Voleva Assumere Tutti**

I primi test furono un disastro comico. Per un semplice progetto di "scrivere 5 email", il `Director` propose un team di 8 persone, tra cui un "Eticista AI" e un "Antropologo Digitale". Aveva interpretato il nostro desiderio di qualità in modo troppo letterale, creando team perfetti ma economicamente insostenibili.

*Logbook del Disastro (27 Luglio):*
```
PROPOSAL: Team di 8 agenti. Costo stimato: 25.000€. Budget: 5.000€.
REASONING: "Per garantire la massima qualità etica e culturale..."
```

**La Lezione Appresa: L'Autonomia ha Bisogno di Vincoli Chiari.**

Un'AI senza vincoli tenderà a "sovra-ottimizzare" la richiesta. Abbiamo imparato che dovevamo essere espliciti sui vincoli, non solo sugli obiettivi. La soluzione fu aggiungere due elementi critici al prompt e alla logica:

1.  **Vincoli Espliciti nel Prompt:** Abbiamo aggiunto le sezioni `**Budget a Disposizione**` e `**Timeline Prevista**`.
2.  **Validazione Post-Generazione:** Il nostro codice esegue un controllo finale: `if proposal.total_cost > budget: raise ValueError("Proposta fuori budget.")`.

Questa esperienza ha rafforzato il **Pilastro #5 (Goal-Driven con Tracking Automatico)**. Un obiettivo non è solo un "cosa", ma anche un "quanto" (budget) e un "quando" (timeline).

---
> **Key Takeaways del Capitolo:**
>
> *   **Tratta gli Agenti come Colleghi:** Progetta i tuoi agenti con profili ricchi (hard/soft skills, personalità). Questo migliora il matching con i task e rende il sistema più intuitivo.
> *   **Delega la Composizione del Team all'AI:** Non hard-codificare i ruoli. Lascia che sia l'AI ad analizzare il progetto e a proporre il team più adatto.
> *   **L'Autonomia Richiede Vincoli:** Per ottenere risultati realistici, devi fornire all'AI non solo gli obiettivi, ma anche i vincoli (budget, tempo, risorse).
> *   **Usa l'AI per la Creatività, il Codice per le Regole:** L'AI è bravissima a generare profili creativi. Il codice è perfetto per applicare regole rigide e non negoziabili (come il rispetto del budget).
---

**Conclusione del Capitolo**

Con il `Director`, il nostro sistema aveva raggiunto un nuovo livello di autonomia. Ora poteva non solo eseguire un piano, ma anche **creare il team giusto per eseguirlo**. Avevamo un sistema che si adattava dinamicamente alla natura di ogni nuovo progetto.

Ma un team, per quanto ben composto, ha bisogno di strumenti per lavorare. La nostra prossima sfida era capire come fornire agli agenti gli "utensili" giusti per ogni mestiere, ancorando le loro capacità intellettuali ad azioni concrete nel mondo reale.
