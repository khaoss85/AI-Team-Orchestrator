### **Capitolo 11 (Versione Estesa): La Cassetta degli Attrezzi dell'Agente – Dalle Funzioni Python agli Agenti come Tool**

**Data:** 27 Luglio

Con il `websearch`, i nostri agenti avevano aperto una finestra sul mondo. Ma un ricercatore esperto non si limita a leggere: analizza dati, esegue calcoli, interagisce con altri sistemi e, se necessario, consulta altri esperti. Per elevare i nostri agenti da semplici "raccoglitori di informazioni" a veri "analisti digitali", dovevamo espandere drasticamente la loro cassetta degli attrezzi.

L'OpenAI Agents SDK classifica i tool in tre categorie principali, e il nostro viaggio ci ha portato a implementarle e a capirne i rispettivi punti di forza e di debolezza.

#### **1. Function Tools: Trasformare il Codice in Capacità**

Questa è la forma più comune e potente di tool. Permette di trasformare **qualsiasi funzione Python in una capacità che l'agente può invocare**. L'SDK si occupa magicamente di analizzare la firma della funzione, i tipi degli argomenti e persino il docstring per generare uno schema che l'LLM può capire.

**La Decisione Architetturale: Un "Tool Registry" Centrale e Decoratori**

Per mantenere il nostro codice pulito e modulare (**Pilastro #14**), abbiamo implementato un `ToolRegistry` centrale. Qualsiasi funzione in qualsiasi punto della nostra codebase può essere trasformata in un tool semplicemente aggiungendo un decoratore.

*Codice di riferimento: `backend/tools/registry.py` e `backend/tools/web_search_tool.py`*

```python
# Esempio di un Function Tool
from .registry import tool_registry

@tool_registry.register("websearch")
class WebSearchTool:
    """
    Esegue una ricerca sul web utilizzando l'API di DuckDuckGo per ottenere informazioni aggiornate.
    È fondamentale per task che richiedono dati in tempo reale.
    """
    async def execute(self, query: str) -> str:
        # Logica per chiamare un'API di ricerca...
        return "Risultati della ricerca..."
```
L'SDK ci ha permesso di definire in modo pulito non solo l'azione (`execute`), ma anche la sua "pubblicità" all'AI tramite il docstring, che diventa la descrizione del tool.

#### **2. Hosted Tools: Sfruttare la Potenza della Piattaforma**

Alcuni tool sono così complessi e richiedono un'infrastruttura così specifica che non ha senso implementarli da soli. Sono i cosiddetti "Hosted Tools", servizi eseguiti direttamente sui server di OpenAI. Il più importante per noi è stato il **`CodeInterpreterTool`**.

**La Sfida: Il `code_interpreter` – Un Laboratorio di Analisi Sandboxed**

Molti task richiedevano analisi quantitative complesse. La soluzione era dare all'AI la capacità di **scrivere ed eseguire codice Python**.

*Codice di riferimento: `backend/tools/code_interpreter_tool.py` (logica di integrazione)*

**"War Story": L'Agente che Voleva Formattare il Disco**

Come raccontato, il nostro primo incontro con il `code_interpreter` è stato traumatico. Un agente ha generato codice pericoloso (`rm -rf /*`), insegnandoci la lezione fondamentale sulla sicurezza.

**La Lezione Appresa: "Zero Trust Execution"**

Il codice generato da un LLM deve essere trattato come l'input più ostile possibile. La nostra architettura di sicurezza si basa su tre livelli:

| Livello di Sicurezza | Implementazione | Scopo |
| :--- | :--- | :--- |
| **1. Sandboxing** | Esecuzione di tutto il codice in un container Docker effimero con permessi minimi (nessun accesso alla rete o al file system host). | Isolare completamente l'esecuzione, rendendo innocui anche i comandi più pericolosi. |
| **2. Analisi Statica** | Un validatore pre-esecuzione che cerca pattern di codice palesemente malevoli (`os.system`, `subprocess`). | Un primo filtro rapido per bloccare i tentativi più ovvi di abuso. |
| **3. Guardrail (Human-in-the-Loop)** | Un `Guardrail` dell'SDK che intercetta il codice. Se tenta operazioni critiche, mette in pausa l'esecuzione e richiede approvazione umana. | La rete di sicurezza finale, che applica il **Pilastro #8** anche alla sicurezza dei tool. |

#### **3. Agents as Tools: Consultare un Esperto**

Questa è la tecnica più avanzata e quella che ha veramente trasformato il nostro sistema in un'**organizzazione digitale**. A volte, il miglior "tool" per un compito non è una funzione, ma un altro agente.

Abbiamo capito che il nostro `MarketingStrategist` non doveva provare a fare un'analisi finanziaria. Doveva *consultare* il `FinancialAnalyst`.

**Il Pattern "Agent-as-Tools":**

L'SDK rende questo pattern incredibilmente elegante con il metodo `.as_tool()`.

*Codice di riferimento: Logica concettuale in `director.py` e `specialist.py`*
```python
# Definizione degli agenti specialistici
financial_analyst_agent = Agent(name="Analista Finanziario", instructions="...")
market_researcher_agent = Agent(name="Ricercatore di Mercato", instructions="...")

# Creazione dell'agente orchestratore
strategy_agent = Agent(
    name="StrategicPlanner",
    instructions="Analizza il problema e delega ai tuoi specialisti usando i tool.",
    tools=[
        financial_analyst_agent.as_tool(
            tool_name="consult_financial_analyst",
            tool_description="Poni una domanda specifica di analisi finanziaria."
        ),
        market_researcher_agent.as_tool(
            tool_name="get_market_data",
            tool_description="Richiedi dati di mercato aggiornati."
        ),
    ],
)
```
Questo ha sbloccato la **collaborazione gerarchica**. Il nostro sistema non era più un team "piatto", ma una vera e propria organizzazione dove gli agenti potevano delegare sotto-compiti, richiedere consulenze e aggregare i risultati, proprio come in un'azienda reale.

---
> **Key Takeaways del Capitolo:**
>
> *   **Scegli la Classe di Tool Giusta:** Non tutti i tool sono uguali. Usa `Function Tools` per capacità custom, `Hosted Tools` per infrastrutture complesse (come il `code_interpreter`) e `Agents as Tools` per la delega e la collaborazione.
> *   **La Sicurezza non è un Optional:** Se usi tool potenti come l'esecuzione di codice, devi progettare un'architettura di sicurezza a più livelli basata sul principio di "Zero Trust".
> *   **La Delega è una Forma Superiore di Intelligenza:** I sistemi di agenti più avanzati non sono quelli in cui ogni agente sa fare tutto, ma quelli in cui ogni agente sa a chi chiedere aiuto.
---

**Conclusione del Capitolo**

Con una cassetta degli attrezzi ricca e sicura, i nostri agenti erano ora in grado di affrontare una gamma molto più ampia di problemi complessi. Potevano analizzare dati, creare visualizzazioni e collaborare a un livello molto più profondo.

Questo, tuttavia, ha reso ancora più critico il ruolo del nostro sistema di qualità. Con agenti così potenti, come potevamo essere sicuri che i loro output, ora molto più sofisticati, fossero ancora di alta qualità e allineati agli obiettivi di business? Questo ci riporta al nostro **Quality Gate**, ma con una nuova e più profonda comprensione di cosa significhi "qualità".
