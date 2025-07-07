
```mermaid
graph TD
    subgraph User Interaction
        A[User] -->|1. POST /workspaces (goal, X-Trace-ID)| B(API Gateway / FastAPI)
    end

    subgraph Backend Core Logic
        B -->|2. Propagates Trace ID| C{Unified Orchestrator}
        C -->|3. Decomposes Goal| D[Goal-Driven Task Planner]
        D -->|4. Creates Tasks| E(Database: tasks)
        C -->|5. Assigns Tasks| F[Agent Manager]
        F -->|6. Selects Agent| G(Database: agents)
        C -->|7. Dispatches Task| H[Executor]
    end

    subgraph Asynchronous Execution
        H -->|8. Executes Task Logic| I(AI Agent: Specialist)
        I -->|9. Records Thought Process| J(Database: thinking_process_steps)
        I -->|10. Generates Results/Artifacts| K(Database: asset_artifacts)
        I -->|11. Logs Actions| L(Database: execution_logs)
        I -->|12. Logs to File| M[File System: server.log]
    end

    subgraph Quality & Delivery
        C -->|13. Monitors Progress| N[Quality Gate]
        N -->|14. Validates Artifacts| K
        C -->|15. Aggregates Results| O[Deliverable Pipeline]
        O -->|16. Publishes Final Deliverable| P(Database: deliverables)
    end

    subgraph Cross-Cutting Concerns
        subgraph Traceability Gap
            style E fill:#f7b2b2,stroke:#c00,stroke-width:2px
            style J fill:#f7b2b2,stroke:#c00,stroke-width:2px
            style K fill:#f7b2b2,stroke:#c00,stroke-width:2px
            style L fill:#f7b2b2,stroke:#c00,stroke-width:2px
            style P fill:#f7b2b2,stroke:#c00,stroke-width:2px
            E -- No `trace_id` column --> X1((X))
            J -- No `trace_id` column --> X2((X))
            K -- No `trace_id` column --> X3((X))
            L -- No `trace_id` column --> X4((X))
            P -- No `trace_id` column --> X5((X))
        end
        B -.-> M
        C -.-> M
        H -.-> M
    end

    style User Interaction fill:#d1e7dd
    style Backend Core Logic fill:#cff4fc
    style Asynchronous Execution fill:#fff3cd
    style Quality & Delivery fill:#f8d7da
```

### Legenda della Mappa

*   **Frecce Solide (`-->`):** Flusso di controllo o dati primario.
*   **Frecce Tratteggiate (`-.->`):** Scrittura nei log (processo trasversale).
*   **Rettangoli:** Componenti software o moduli.
*   **Rettangoli con angoli arrotondati:** Tabelle del database o file.
*   **Rombi:** Punti decisionali o di orchestrazione.
*   **Cerchi con la X Rossa:** Indicano la **mancanza critica** della colonna `trace_id` nelle tabelle del database, che interrompe la catena di tracciabilità.

Questa mappa illustra il flusso ideale dal punto di vista architetturale, ma evidenzia visivamente dove la tracciabilità end-to-end si interrompe a causa delle lacune nello schema del database.
