# Architettura degli Agenti AI: Un Sistema a Ciclo Chiuso

Questo documento descrive l'architettura, i principi e il funzionamento del sistema di agenti AI che alimenta questa applicazione. Il nostro approccio si basa su una filosofia 100% AI-Driven, dove la logica di business, le decisioni e l'apprendimento sono delegati a un'orchestra di agenti intelligenti.

## 1. Architettura a Flusso Continuo: La "Cucina AI"

Il nostro sistema non è una semplice catena di montaggio, ma un ciclo di feedback continuo che apprende e si migliora a ogni esecuzione. Possiamo immaginarlo come una cucina gourmet AI:

1.  **Pianificazione (La Ricetta):** Un **Agente Analista** scompone un obiettivo complesso in task più piccoli e un **Validatore di Tool** si assicura che la "ricetta" richieda solo "ingredienti freschi" (dati reali ottenuti tramite tool).
2.  **Esecuzione (La Preparazione):** Un **Team di Agenti Dinamici**, creato su misura dall'AI per ogni progetto, esegue i task raccogliendo i dati necessari.
3.  **Produzione (La Cottura):** Un set di **Agenti di Produzione** prende i risultati grezzi e li trasforma in un deliverable coerente e di alta qualità, arricchendolo con la conoscenza storica del sistema.
4.  **Valutazione (Il Controllo Qualità):** Una **Commissione di Qualità AI** analizza il deliverable finale, valutandone il valore di business, la completezza e l'azionabilità.
5.  **Apprendimento (Il Miglioramento della Ricetta):** I risultati di successo e di fallimento vengono salvati nella **Memoria** del sistema come "pattern". Questo permette al ciclo di ricominciare in modo più intelligente la volta successiva.

Questo ciclo chiuso garantisce che il sistema non solo esegua, ma apprenda e si evolva in modo autonomo.

## 2. Gli Agenti del Sistema

Gli agenti si dividono in due categorie:

### Agenti Dinamici (Il Team di Progetto)

Questi agenti sono gli **esecutori** dei task. Non sono fissi, ma vengono **proposti e creati dall'AI** in base agli obiettivi specifici di ogni workspace. Questo garantisce massima flessibilità e scalabilità.

*   **Numero:** Variabile (N per workspace).
*   **Esempi di Ruoli:** Project Manager, Lead Developer, QA Specialist, UX/UI Designer.
*   **Principio Guida:** Creare un team su misura con competenze complementari per evitare sovrapposizioni.

### Agenti Fissi (Il Sistema Operativo AI)

Questi 8 agenti sono l'infrastruttura che garantisce il funzionamento della piattaforma. Lavorano in background su tutti i progetti.

**A. Pianificazione e Analisi (2 Agenti)**
1.  **AnalystAgent:** Scompone gli obiettivi in task.
2.  **AIToolAwareValidator:** Determina quali tool sono necessari per garantire risultati basati su dati reali.

**B. Produzione dei Deliverable (3 Agenti)**
3.  **AssetExtractorAgent:** Estrae informazioni strutturate dai risultati dei task.
4.  **MemoryEnhancedAIAssetGenerator:** Genera il contenuto del deliverable usando i dati raccolti e la memoria.
5.  **DeliverableAssemblyAgent:** Assembla il contenuto nel formato finale.

**C. Controllo Qualità (2 Agenti)**
6.  **AssetQualityEvaluator:** Valuta la qualità e il valore di business di ogni contenuto generato.
7.  **PlaceholderDetector:** Si assicura che non ci siano testi generici o placeholder.

**D. Memoria e Apprendimento (1 Agente)**
8.  **SemanticSearchAgent:** Cerca in modo intelligente nella memoria del sistema per recuperare pattern di successo o fallimento.

## 3. Il Ragionamento Strategico degli Agenti (Esempi di Prompt)

Gli agenti non eseguono ciecamente. Vengono guidati da prompt progettati per forzarli a un ragionamento strategico.

### Esempio 1: Il Validatore di Tool (AIToolAwareValidator)

Questo prompt costringe l'agente a pensare come un analista strategico, non come un semplice esecutore.

```python
prompt = f"""
Analizza quale tools dovrebbero essere usati per completare questo task in modo professionale.

TASK: {task_name}
OBJECTIVE: {task_objective}
BUSINESS CONTEXT: {json.dumps(business_context or {}, indent=2)}

AVAILABLE TOOLS:
{', '.join(self.available_tools)}

ANALISI RICHIESTA:
1. Quali tools sono ESSENZIALI per completare questo task con dati reali?
2. Quali tools sono OPZIONALI ma migliorerebbero la qualità?
3. Perché ogni tool è necessario per questo specifico objective?

Rispondi in JSON:
{{
    "required_tools": ["tool1", "tool2"],
    "optional_tools": ["tool3"],
    "tool_justification": {{
        "tool1": "perché è essenziale per...",
        "tool2": "necessario per raccogliere..."
    }},
    "expected_data_types": ["tipo di dato che ogni tool dovrebbe fornire"],
    "confidence": 0-100
}}
"""
```

### Esempio 2: Il Valutatore di Qualità (AssetQualityEvaluator)

Questo prompt trasforma la valutazione da un semplice "sì/no" a un'analisi di business completa, che include suggerimenti per il miglioramento.

```python
prompt = f"""You are a Quality Assurance expert. Evaluate the following asset based on the provided goal context.

**Goal Context:**
- **Description:** {goal_context.get('description', 'N/A')}
- **Metric:** {goal_context.get('metric_type', 'N/A')}

**Asset to Evaluate:**
```json
{{
  "asset_type": "{artifact_type}",
  "content": {json.dumps(artifact_content, indent=2)}
}}
```

**Evaluation Criteria:**
1.  **Business Value (0-100):** How valuable is this asset for achieving the business goal?
2.  **Completeness (0-100):** Does the asset fully address the goal?
3.  **Clarity & Readability (0-100):** Is the content clear and well-structured?
4.  **Actionability (0-100):** Can a user take immediate, concrete actions based on this asset?

**Output Format (JSON only):**
{{
  "quality_score": <average_score>,
  "scores": {{
    "business_value": <score>,
    "completeness": <score>,
    "clarity": <score>,
    "actionability": <score>
  }},
  "reasoning": "Provide a detailed explanation for your scores.",
  "improvement_suggestions": [
    "Suggestion 1: Be more specific about...",
    "Suggestion 2: Include real data points for..."
  ]
}}
"""
```

## 4. Sfide Superate e Soluzioni Architetturali

*   **Sfida:** Evitare la generazione di contenuti "placeholder" o di basso valore.
    *   **Soluzione:** L'**AIToolAwareValidator** agisce come un "quality gate" preventivo, forzando l'uso di tool che raccolgono dati reali prima ancora che la generazione del contenuto inizi.

*   **Sfida:** Rischio di "single point of failure" affidando la qualità a un solo agente.
    *   **Soluzione:** L'architettura implementa un **"Consenso AI a più livelli"**. L'agente di qualità (`AssetQualityEvaluator`) non agisce come un singolo giudice, ma orchestra una "commissione" di pareri da specialisti AI (es. uno per il valore di business, uno per la veridicità dei dati) prima di sintetizzare una decisione finale.

## 5. Opportunità di Miglioramento Future

Il sistema è progettato per evolvere. Le prossime iterazioni potrebbero includere:

*   **Unificazione degli Agenti di Qualità:** Fondere le responsabilità del `PlaceholderDetector` all'interno dell'`AssetQualityEvaluator` per creare un unico punto di responsabilità per la qualità, rendendo l'architettura ancora più snella.
*   **Introduzione di Agenti Strategici:**
    1.  **Human Feedback Coordinator:** Per gestire in modo più fluido le interazioni e le approvazioni umane.
    2.  **Efficiency Optimizer:** Per monitorare i costi e le performance, suggerendo l'uso di modelli AI più efficienti in base al task.
    3.  **Strategic Planner:** L'evoluzione finale. Un agente in grado di analizzare i successi passati e le condizioni di mercato per proporre in modo proattivo nuovi obiettivi di business.
