# MLOps Pipeline Architecture Diagram — Experiment 10

This document illustrates the end-to-end continuous integration, continuous delivery (CI/CD), secret injection, execution, and monitoring pipeline for the **Task Automation Agent**.

---

## 1. Complete End-to-End MLOps Pipeline

```mermaid
flowchart TD
    subgraph DEV["1. Local Development (Windows 11)"]
        D1["Developer edits code (app.py, agent.py)"] --> D2["Local Virtual Env (.venv)"]
        D2 --> D3["Local Pytest Suite (27 Mocked Unit Tests)"]
        D3 --> D4["Local Git Commit (Secrets Excluded by .gitignore)"]
    end

    subgraph CI["2. GitHub Actions CI Pipeline (.github/workflows/ci.yml)"]
        D4 -->|"git push origin main"| G1["GitHub Repository"]
        G1 --> G2["Trigger CI Workflow"]
        G2 --> G3["Checkout Code (actions/checkout@v4)"]
        G3 --> G4["Setup Python 3.11 Environment"]
        G4 --> G5["Install Pinned Dependencies"]
        G5 --> G6["Bytecode & Syntax Check (py_compile)"]
        G6 --> G7["Automated Pytest Execution"]
        G7 --> G8["Docker Container Build Verification"]
        G8 --> G9{"CI Status Check"}
        G9 -- "Pass" --> G10["Green CI Badge ✅"]
        G9 -- "Fail" --> G11["Pipeline Break & Alert ❌"]
    end

    subgraph DEPLOY["3. Continuous Deployment (Hugging Face Spaces / Local Docker)"]
        G10 --> H1["Hugging Face Docker Space SDK"]
        H1 --> H2["Build Dockerfile (UID 1000 appuser)"]
        H2 --> H3["Runtime Secret Injection (GROQ_API_KEY)"]
        H3 --> H4["Start Streamlit Server (Port 7860/8501)"]
    end

    subgraph AGENT["4. Runtime Agent Execution"]
        U1["User Enters Research Topic"] --> A1["Streamlit Web UI"]
        A1 --> A2["Input Length & Format Validation"]
        A2 --> A3["DuckDuckGo Live Search Engine"]
        A3 --> A4["Result Cleaning, Filtering & Deduplication"]
        A4 --> A5["Groq Cloud LLM (llama-3.3-70b-versatile)"]
        A5 --> A6["Parse Strictly 3 Bullet Points"]
        A6 --> A7["Render 3-Point Brief & Clickable Source URLs"]
    end

    subgraph OBS["5. Observability & Telemetry"]
        A7 --> O1["Python Logging Module (stdout/stderr)"]
        A7 --> O2["Latency Timers (time.perf_counter)"]
        A7 --> O3["In-Memory Operational Metrics (Sidebar)"]
    end

    H4 --> AGENT
```

---

## 2. Component Interaction & Data Flow

```mermaid
sequenceDiagram
    autonumber
    actor User as Student / User
    participant UI as Streamlit UI (app.py)
    participant Agent as Agent Controller (agent.py)
    participant DDG as DuckDuckGo Search API
    participant Groq as Groq Cloud LLM
    participant Metrics as Telemetry / Logger

    User->>UI: Enter Topic & Click "Generate Brief"
    UI->>Agent: run_research_agent(topic)
    Agent->>Agent: validate_topic()
    Agent->>Metrics: Log Request Received & Start Timer
    Agent->>DDG: search_web(topic, max_results=5)
    DDG-->>Agent: Raw search results
    Agent->>Agent: clean_search_results() (filter & deduplicate)
    Agent->>Groq: chat.completions.create(model, messages, temp=0.2)
    Groq-->>Agent: Formatted summary response
    Agent->>Agent: parse_bullet_points() (ensure exactly 3)
    Agent->>Metrics: Record Latencies & Success Counts
    Agent-->>UI: Structured Brief Dict (Bullets, Sources, Timings)
    UI-->>User: Display 3-Point Card, Source Citations & Latency Badges
```

---

## 3. Secret Management & Isolation Model

```mermaid
flowchart LR
    subgraph UNSECURE["Exposed Paths (PROTECTED)"]
        A[".git Repository"]
        B["Docker Image Layers"]
        C["Console / Terminal Logs"]
        D["GitHub Actions Logs"]
    end

    subgraph SECURE["Protected Injections"]
        S1["Local Developer: .env file (Git-Ignored)"]
        S2["Cloud Deployment: HF Spaces Secrets / GH Secrets"]
        S3["Streamlit UI: Masked Key Display (gsk_...xyz)"]
    end

    S1 -. "Never committed" .-> A
    S2 -. "Injected at runtime only" .-> B
    S3 -. "Credentials scrubbed" .-> C
    S3 -. "Zero secrets in tests" .-> D
```
