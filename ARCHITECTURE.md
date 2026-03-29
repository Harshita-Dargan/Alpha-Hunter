# 🏛️ Alpha-Hunter: System Architecture

This document provides a high-level overview of the data flow, the autonomous agent grid, and the technological stack powering **Alpha-Hunter**. 

## High-Level Data Flow

At its core, **Alpha-Hunter** operates on a modern decoupled architecture. The user interface acts as a thin, highly responsive client that offloads all heavy analytical lifting to an asynchronous Python engine. 

1. **Ingestion Layer:** The user interacts with the Glassmorphism UI, dropping unstructured data (like messy PDFs) or structural ledgers (CSVs) into the application.
2. **Routing & Dispatch:** The Vanilla JS frontend sends POST requests payloading the data to the FastAPI router.
3. **The Cognitive Swarm:** 
    - The backend parses the data and awakens a suite of distinct Python scripts (the "Agents"), each responsible for a specific domain (Quant, Risk, Tax, NLP Extraction, Scenarios, and Live News).
    - These agents simultaneously synthesize the data using algorithmic methods (e.g., PyXIRR for mathematical returns) and generative methods (e.g., Google's Gemini 1.5).
4. **Resilience & Caching:** To guarantee high availability and protect against API Quota Exhaustion (`429 Too Many Requests`), a custom monkey-patched middleware sits between the Agents and Google's LLM. This caches exact prompt hashes to a local `.gemini_cache` disk store, serving repeat queries instantly holding API costs to an absolute minimum.
5. **Presentation:** The aggregated insights are packaged into a structured JSON response to the frontend, instantly expanding the visual dashboard.

---

## 🏗️ Architecture Diagram

```mermaid
graph TD
    classDef user fill:#2c2c2c,stroke:#fff,stroke-width:2px,color:#fff
    classDef ui fill:#0a192f,stroke:#64ffda,stroke-width:2px,color:#64ffda
    classDef api fill:#112240,stroke:#64ffda,stroke-width:2px,color:#ccd6f6,stroke-dasharray: 5 5
    classDef backend fill:#112240,stroke:#8892b0,stroke-width:2px,color:#ccd6f6
    classDef agent fill:#233554,stroke:#ff7b72,stroke-width:2px,color:#e6f1ff
    classDef cache fill:#2d1b2e,stroke:#d299ff,stroke-width:2px,color:#f0e6fa
    classDef llm fill:#1c2d42,stroke:#58a6ff,stroke-width:2px,color:#e6f1ff
    classDef ext fill:#2c3e50,stroke:#f39c12,stroke-width:2px,color:#ecf0f1

    U((User)):::user -->|Uploads PDF/CSV or<br>Clicks Scenario| FE[Frontend UI<br>Vanilla JS / Glassmorphism]:::ui
    
    subgraph FastAPI_Server ["FastAPI Asynchronous Engine"]
        FE -->|POST /api/analyze-csv<br>POST /api/analyze-pdf<br>POST /api/scenario| Router{API Router}:::api
        
        Router -->|Routes| BA[Backend Controllers<br>main.py]:::backend
        
        subgraph Autonomous_Agents ["Swarm of Cognitive Agents"]
            BA --> QA[Quant Agent<br>PyXIRR]:::agent
            BA --> RA[Risk Auditor]:::agent
            BA --> TA[Tax Strategist]:::agent
            BA --> NO[News Oracle<br>ET RSS Sync]:::agent
            BA --> PA[PDF Analyst<br>OCR Extractor]:::agent
            BA --> SA[Scenario Evaluators<br>Bulk/Breakout/Macro]:::agent
        end
        
        NO -.->|Fetches Live Headlines| GoogleNews((Google News RSS)):::ext
        
        AgentSwarm((Agents)):::agent
        QA -.-> AgentSwarm
        RA -.-> AgentSwarm
        TA -.-> AgentSwarm
        NO -.-> AgentSwarm
        PA -.-> AgentSwarm
        SA -.-> AgentSwarm
        
        subgraph Gemini_Integration ["LLM Inference Engine"]
            AgentSwarm -->|Generates Content| CacheLayer[Monkey-Patched Interceptor<br>MD5 Hash Disk Cache]:::cache
            CacheLayer -->|Cache Miss| GeminiAPI[Google Gemini 1.5 API]:::llm
            CacheLayer -->|Cache Hit| LocalDisk[(Local JSON Store)]:::cache
        end
    end
    
    GeminiAPI -->|Returns Synthesized Insights| CacheLayer
    CacheLayer -->|Returns Data| AgentSwarm
    AgentSwarm -->|Aggregates Dashboard JSON| BA
    BA -->|Yields Parsed Data| FE
    FE -->|Renders UI / Charts| U
```

---

## 🛡️ Security & Scalability

- **API Protection:** The local MD5-hash cache intercepts backend inference generation globally. Identical AI evaluations cost $0 and take 0ms after the first request.
- **Data Privacy:** Local `pandas` dataframes and `.env` isolation ensures the user's base brokerage data and developer keys never leak beyond their designated execution loop.
- **Asynchronous Design:** Leveraging FastAPI and Uvicorn thread-pooling ensures that waiting for the LLM to write a "Risk Strategy" does not freeze the UI or block concurrent user operations.
