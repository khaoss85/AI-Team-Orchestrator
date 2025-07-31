### **Capitolo 10: Il Test sui Tool – Ancorare l'AI alla Realtà**

**Data:** 27 Luglio

Avevamo un team dinamico e un orchestratore intelligente. Ma gli agenti, per quanto ben progettati, erano ancora dei "filosofi digitali". Potevano ragionare, pianificare e scrivere, ma non potevano **agire sul mondo esterno**. La loro conoscenza era limitata a quella intrinseca del modello LLM, un'istantanea del passato, priva di dati in tempo reale.

Un sistema AI che non può accedere a informazioni aggiornate è destinato a produrre contenuti generici, obsoleti e, in ultima analisi, inutili. Per rispettare il nostro **Pilastro #11 (Deliverable Concreti e Azionabili)**, dovevamo dare ai nostri agenti la capacità di "vedere" e "interagire" con il mondo esterno. Dovevamo dar loro dei **Tool**.

#### **La Decisione Architetturale: Un "Tool Registry" Centrale**

La nostra prima decisione fu di non associare i tool direttamente ai singoli agenti nel codice. Questo avrebbe creato un forte accoppiamento e reso difficile la gestione. Invece, abbiamo creato un **Tool Registry centralizzato**.

*Codice di riferimento: `backend/tools/registry.py` (ipotetico, basato sulla nostra logica)*

Questo registry è un semplice dizionario che mappa un nome di tool (es. `"websearch"`) a una classe eseguibile.

```python
# tools/registry.py
class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def register(self, tool_name):
        def decorator(tool_class):
            self._tools[tool_name] = tool_class()
            return tool_class
        return decorator

    def get_tool(self, tool_name):
        return self._tools.get(tool_name)

tool_registry = ToolRegistry()

# tools/web_search_tool.py
from .registry import tool_registry

@tool_registry.register("websearch")
class WebSearchTool:
    async def execute(self, query: str):
        # Logica per chiamare un'API di ricerca come DuckDuckGo
        ...
```

Questo approccio ci ha dato un'incredibile flessibilità:

*   **Modularità (Pilastro #14):** Ogni tool è un modulo a sé stante, facile da sviluppare, testare e mantenere.
*   **Riusabilità:** Qualsiasi agente nel sistema può richiedere l'accesso a qualsiasi tool registrato, senza bisogno di codice specifico.
*   **Estensibilità:** Aggiungere un nuovo tool (es. un `ImageGenerator`) significa semplicemente creare un nuovo file e registrarlo, senza toccare la logica degli agenti o dell'orchestratore.

#### **Il Primo Tool: `websearch` – La Finestra sul Mondo**

Il primo e più importante tool che abbiamo implementato è stato `websearch`. Questo singolo strumento ha trasformato i nostri agenti da "studenti in una biblioteca" a "ricercatori sul campo".

Quando un agente deve eseguire un task, l'SDK di OpenAI gli permette di decidere autonomamente se ha bisogno di un tool. Se l'agente "pensa" di aver bisogno di cercare sul web, l'SDK formatta una richiesta di esecuzione del tool. Il nostro `Executor` intercetta questa richiesta, chiama la nostra implementazione del `WebSearchTool` e restituisce il risultato all'agente, che può quindi usarlo per completare il suo lavoro.

**Flusso di Esecuzione di un Tool:**

```mermaid
graph TD
    A[Agente riceve Task] --> B{AI decide di usare un tool};
    B --> C[SDK formatta richiesta per "websearch"];
    C --> D{Executor intercetta la richiesta};
    D --> E[Chiama `tool_registry.get_tool('websearch')`];
    E --> F[Esegue la ricerca reale];
    F --> G[Restituisce i risultati all'Executor];
    G --> H[SDK passa i risultati all'Agente];
    H --> I[Agente usa i dati per completare il Task];
```

#### **"War Story": Il Test che ha Svelato la "Pigrizia" dell'AI**

Abbiamo scritto un test per verificare che i tool funzionassero.

*Codice di riferimento: `tests/test_tools.py`*

Il test era semplice: dare a un agente un task che *richiedeva* palesemente una ricerca web (es. "Qual è l'attuale CEO di OpenAI?") e verificare che il tool `websearch` venisse chiamato.

I primi risultati furono sconcertanti: **il test falliva il 50% delle volte.**

*Logbook del Disastro (27 Luglio):*
```
ASSERTION FAILED: Web search tool was not called.
AI Response: "As of my last update in early 2023, the CEO of OpenAI was Sam Altman."
```

**Il Problema:** L'LLM era "pigro". Invece di ammettere di non avere informazioni aggiornate e usare il tool che gli avevamo fornito, preferiva dare una risposta basata sulla sua conoscenza interna, anche se obsoleta. Stava scegliendo la via più facile, a discapito della qualità e della veridicità.

**La Lezione Appresa: Bisogna *Forzare* l'Uso dei Tool**

Non basta *dare* un tool a un agente. Bisogna creare un ambiente e delle istruzioni che lo **incentivino (o lo costringano) a usarlo**.

La soluzione è stata un raffinamento del nostro prompt engineering:

1.  **Istruzioni Esplicite nel System Prompt:** Abbiamo aggiunto una frase al prompt di sistema di ogni agente:
    > *"La tua conoscenza è limitata. Per qualsiasi informazione che richieda dati aggiornati o specifici del mondo reale, **DEVI** usare il tool `websearch`. Non dare mai risposte basate solo sulla tua memoria interna se sospetti che i dati possano essere obsoleti."*

2.  **"Priming" nel Prompt del Task:** Quando assegnavamo un task, abbiamo iniziato ad aggiungere un suggerimento:
    > *"Obiettivo: Qual è l'attuale CEO di OpenAI? (Suggerimento: usa il tool `websearch` per trovare informazioni aggiornate)."*

Queste modifiche hanno aumentato l'utilizzo del tool dal 50% a oltre il 95%, risolvendo il problema della "pigrizia" e garantendo che i nostri agenti cercassero attivamente dati reali.

---
> **Key Takeaways del Capitolo:**
>
> *   **Gli Agenti Hanno Bisogno di Tool:** Un sistema AI senza accesso a strumenti esterni è un sistema limitato e destinato a diventare obsoleto.
> *   **Centralizza i Tool in un Registry:** Non legare i tool a agenti specifici. Un registry modulare è più scalabile e manutenibile.
> *   **L'AI può essere "Pigra":** Non dare per scontato che un agente userà i tool che gli fornisci. Devi istruirlo e incentivarlo esplicitamente a farlo.
> *   **Testa il *Comportamento*, non solo l'Output:** I test sui tool non devono verificare solo che il tool funzioni, ma che l'agente *decida* di usarlo quando è strategicamente corretto.
---

**Conclusione del Capitolo**

Con l'introduzione dei tool, i nostri agenti avevano finalmente un modo per produrre risultati basati sulla realtà. Ma questo ha aperto un nuovo vaso di Pandora: la **qualità**.

Ora che gli agenti potevano produrre contenuti ricchi di dati, come potevamo essere sicuri che questi contenuti fossero di alta qualità, coerenti e, soprattutto, di reale valore per il business? Era il momento di costruire il nostro **Quality Gate**.
