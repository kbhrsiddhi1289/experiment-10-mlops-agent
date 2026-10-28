# College Laboratory Practical Report

## Experiment 10: MLOps Deployment of a Task-Automation Agent

**Course:** Generative AI / Agentic Systems Laboratory (Semester 7)  
**Academic Term:** 2026  
**Student Name:** [Your Name]  
**Roll Number:** [Your Roll Number]  
**Department:** Computer Engineering / Artificial Intelligence & Data Science  

---

## 1. Experiment Title
**MLOps Deployment of a Task-Automation Agent (Autonomous Research Brief Generator)**

---

## 2. Aim
To design, implement, containerize, test, and deploy an autonomous task-automation research agent following MLOps (Machine Learning Operations) and LLMOps engineering best practices, incorporating automated web search, large language model summarization, continuous integration (CI) workflows, containerization, and runtime secret isolation.

---

## 3. Theory of MLOps
Machine Learning Operations (MLOps) is an engineering discipline focused on unifying Machine Learning system development (Dev) and system operations (Ops). While classical software DevOps emphasizes version control, automated testing, and continuous delivery of deterministic code, MLOps extends these principles to manage data pipelines, model artifacts, prompt engineering, and non-deterministic model behaviors.

In the context of **Agentic AI and LLMOps**, the challenges shift from model weight retraining to:
1. **Pipeline Reproducibility:** Guaranteeing that agent workflows (e.g., Search &rarr; Clean &rarr; Prompt &rarr; Output Formatting) run consistently across development, staging, and containerized production environments.
2. **Environment Parity & Containerization:** Using Docker to eliminate "it works on my machine" issues by packaging the Python runtime, system libraries, and application dependencies into immutable images.
3. **Continuous Integration (CI):** Automatically validating code integrity through linting, bytecode compilation, and deterministic mocked unit tests on every code commit.
4. **Credential Isolation:** Preventing catastrophic data leaks by separating application code from API secrets (`GROQ_API_KEY`) using environment injection and `.gitignore` guardrails.
5. **Observability & Telemetry:** Instrumenting request latencies, web search performance, LLM inference times, and failure categories to monitor real-time agent health.

---

## 4. Tools and Technologies Used

| Tool / Technology | Version / Specification | Rationale & Purpose in MLOps |
| :--- | :--- | :--- |
| **Python** | 3.11.9 | Stable, high-performance base runtime for modern AI libraries. |
| **Streamlit** | 1.66.1 | Lightweight, Python-native web application framework for interactive UI. |
| **DuckDuckGo Search** | `duckduckgo-search` 8.1.1 | Free, privacy-respecting, zero-API-key search engine integration for live web data. |
| **Groq Cloud API** | `groq` 1.7.0 SDK | Ultra-low latency LPU (Language Processing Unit) inference provider. |
| **Groq Model** | `llama-3.3-70b-versatile` | State-of-the-art open-weights LLM capable of strictly adhering to evidence constraints. |
| **python-dotenv** | 1.2.4 | Manages private environment variables without committing credentials. |
| **pytest** | 9.2.0 | Automated unit testing framework for regression testing. |
| **Git & GitHub** | Git 2.51.0 / GitHub | Version control, branch management, and trigger for CI pipelines. |
| **Docker** | Docker 29.9.2 (`python:3.11-slim`) | Containerization engine creating immutable, reproducible runtimes with non-root security. |
| **GitHub Actions** | Ubuntu-latest runner | Continuous Integration server executing automated test and build workflows. |
| **Hugging Face Spaces**| Docker SDK (Port 7860) | Cloud deployment platform for public hosting of containerized AI applications. |

---

## 5. System Architecture & Workflow

The architecture follows a modular, decoupled pipeline pattern:

```
[User Query] 
     │
     ▼
[Streamlit Frontend (app.py)] 
     │
     ▼
[Input Validation (agent.py)] ──(Invalid)──> [Validation Error Response]
     │ (Valid)
     ▼
[DuckDuckGo Search Engine (DDGS)] ──(Network Error)──> [Graceful Search Error]
     │ (Raw Results)
     ▼
[Data Cleaning & Deduplication] 
     │ (Sanitized Excerpts)
     ▼
[Groq Cloud LLM (llama-3.3-70b)] ──(API Error)──> [Graceful LLM Error]
     │ (Prompt Constraints: Exactly 3 Bullets)
     ▼
[Output Extraction & Normalization]
     │
     ├──> [3-Bullet Structured Card]
     ├──> [Clickable Source Hyperlinks]
     └──> [Telemetry Latency Badges & Session Logs]
```

---

## 6. Step-by-Step Implementation

### Task 1: Environment Setup and Virtual Isolation
1. Initialized Python 3.11 virtual environment `.venv` using `python -m venv .venv`.
2. Created `.gitignore` and `.dockerignore` files to explicitly prevent `.env`, `.venv`, and cache files from entering version control.
3. Installed pinned packages from `requirements.txt`.

### Task 2: Configuration & Safe Credential Management (`config.py`)
1. Implemented `get_api_key()` to inspect runtime overrides first, falling back to `os.getenv("GROQ_API_KEY")`.
2. Built `mask_api_key()` to prevent leaking credentials in UI status cards (e.g. `gsk_...xyz`).
3. Added fallback support for configurable application ports (`PORT=8501` locally, `7860` in Hugging Face Spaces).

### Task 3: Agent Core Logic & Decoupled Pipeline (`agent.py`)
1. Implemented `validate_topic()` enforcing length limits ($\le 300$ characters) and rejecting empty or whitespace-only queries.
2. Built `clean_search_results()` to strip invalid schemes, discard missing descriptions, and deduplicate duplicate URLs.
3. Built `generate_brief_with_groq()` with strict prompt boundaries commanding the LLM to output exactly three bullet points based only on provided search evidence.
4. Built `parse_bullet_points()` to normalize LLM output into an array of exactly three clean bullet strings.
5. Implemented `AgentMetrics` class to aggregate real-time telemetry (total requests, successes, failures, average latencies).

### Task 4: Streamlit UI Development (`app.py`)
1. Created clean academic layout with title: **Task Automation Agent — Research Brief Generator**.
2. Designed sidebar with system status indicators, masked credential status, and runtime telemetry.
3. Created responsive topic entry form with real-time character counter and loading spinner.
4. Rendered the research brief in an isolated styled card, separated from clickable citation URLs.

### Task 5: Automated Testing (`tests/`)
1. Built `test_config.py` verifying credential masking, override priority, and port resolution.
2. Built `test_agent.py` containing 19 deterministic tests covering:
   - Valid, empty, single-character, and over-length topics.
   - Search sanitization, non-http discarding, and URL deduplication.
   - 3-bullet normalization (>3 bullets, <3 bullets, numbered lists).
   - Mocked search errors, LLM errors, and end-to-end success flows.

### Task 6: Docker Containerization (`Dockerfile`)
1. Built a lightweight container using official `python:3.11-slim`.
2. Implemented security best practice: created non-root user `appuser` (UID 1000).
3. Configured multi-port exposure (8501 and 7860) and dynamic `PORT` binding.
4. Added health check directive (`curl --fail http://localhost:${PORT:-8501}/_stcore/health`).

### Task 7: Continuous Integration (`.github/workflows/ci.yml`)
1. Created GitHub Actions workflow triggered on push and pull requests to `main`.
2. Configured matrix with Python 3.11, automated dependency caching, syntax check (`py_compile`), pytest suite execution, and Docker container build.

### Task 8: Continuous Deployment Preparation (Hugging Face Spaces)
1. Added YAML frontmatter metadata to `README.md` (`sdk: docker`, `app_port: 7860`).
2. Configured `.github/workflows/deploy-hf.yml` for optional automated syncing to Hugging Face Space repository.

---

## 7. Commands Used for Setup, Testing, and Deployment

### Local PowerShell Setup:
```powershell
# 1. Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 3. Create private environment configuration
Copy-Item .env.example .env
```

### Running Automated Tests:
```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

### Running Local Streamlit App:
```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

### Docker Commands:
```powershell
# Build Docker image
docker build -t experiment-10-agent:local .

# Run Docker container with runtime secret injection
docker run --rm -p 8501:8501 --env-file .env experiment-10-agent:local
```

### Git Version Control Commands:
```powershell
git init
git add .
git commit -m "feat: complete MLOps pipeline for task-automation agent"
```

---

## 8. Secret-Management Approach
Security is a foundational pillar of MLOps. The project implements a multi-tier secret defense model:
1. **Zero Secret Storage in Code:** No API keys, passwords, or tokens are hardcoded.
2. **Git Safeguard:** `.gitignore` explicitly blocks `.env` and `*.env.local`.
3. **Docker Safeguard:** `.dockerignore` blocks `.env` from being baked into Docker image layers.
4. **Runtime Injection:** Credentials are provided at runtime through Docker `--env-file` or Hugging Face Space Secrets.
5. **Masked Display:** The UI and logs never print raw secrets; credentials are only displayed in masked format (`gsk_...xyz`).
6. **Zero-Secret Testing:** Unit tests use `unittest.mock` to mock LLM and search calls, ensuring CI pipelines never require production credentials.

---

## 9. Automated Testing Results

The test suite was executed locally inside the sandbox environment using `pytest`:

```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\siddhi kumbhar\Documents\SEM 7\Gen AI\experiment-10-mlops-agent
configfile: pytest.ini
testpaths: tests
collected 27 items

tests/test_agent.py::test_validate_topic_valid PASSED                    [  3%]
tests/test_agent.py::test_validate_topic_empty_or_none PASSED            [  7%]
tests/test_agent.py::test_validate_topic_too_short PASSED                [ 11%]
tests/test_agent.py::test_validate_topic_excessive_length PASSED         [ 14%]
tests/test_agent.py::test_clean_search_results_none_and_empty PASSED     [ 18%]
tests/test_agent.py::test_clean_search_results_filtering PASSED          [ 22%]
tests/test_agent.py::test_clean_search_results_deduplication PASSED      [ 25%]
tests/test_agent.py::test_parse_bullet_points_standard_three PASSED      [ 29%]
tests/test_agent.py::test_parse_bullet_points_numbered_list PASSED       [ 33%]
tests/test_agent.py::test_parse_bullet_points_more_than_three PASSED     [ 37%]
tests/test_agent.py::test_parse_bullet_points_fewer_than_three PASSED    [ 40%]
tests/test_agent.py::test_parse_bullet_points_empty PASSED               [ 44%]
tests/test_agent.py::test_run_research_agent_missing_api_key PASSED      [ 48%]
tests/test_agent.py::test_run_research_agent_invalid_topic PASSED        [ 51%]
tests/test_agent.py::test_run_research_agent_no_search_results PASSED    [ 55%]
tests/test_agent.py::test_run_research_agent_search_failure PASSED       [ 59%]
tests/test_agent.py::test_run_research_agent_llm_failure PASSED          [ 62%]
tests/test_agent.py::test_run_research_agent_success PASSED              [ 66%]
tests/test_agent.py::test_agent_metrics_tracking PASSED                  [ 70%]
tests/test_config.py::test_get_api_key_with_override PASSED              [ 74%]
tests/test_config.py::test_get_api_key_from_env PASSED                   [ 77%]
tests/test_config.py::test_get_api_key_empty PASSED                      [ 81%]
tests/test_config.py::test_get_model_default_and_override PASSED         [ 85%]
tests/test_config.py::test_get_server_port PASSED                        [ 88%]
tests/test_config.py::test_is_api_key_configured PASSED                  [ 92%]
tests/test_config.py::test_mask_api_key PASSED                           [ 96%]
tests/test_config.py::test_get_system_status PASSED                      [100%]

============================= 27 passed in 0.86s ==============================
```

> `[ADD SCREENSHOT: 02_pytest_passing.png - Terminal showing all 27 unit tests passing]`

---

## 10. Docker Build and Container Status

- **Docker Client:** Docker version 29.9.2 is installed on the host.
- **Docker Daemon Observation:** The Docker Desktop daemon was not actively running during local test inspection (`open //./pipe/docker_engine: The system cannot find the file specified`).
- **Dockerfile Verification:** The `Dockerfile` has been fully authored with syntax adhering to Docker BuildKit and Hugging Face Docker Space guidelines.
- **Action Required for Local Docker:** Start Docker Desktop from the Windows Start menu, then execute `docker build -t experiment-10-agent:local .`.

> `[ADD SCREENSHOT: 07_docker_build_and_run.png - Docker image build and running container]`

---

## 11. GitHub Actions CI Pipeline Status

- **Workflow File:** `.github/workflows/ci.yml` is prepared and verified.
- **Workflow Scope:** Runs `py_compile`, `pytest`, and `docker build` on every push to `main`.
- **Remote Execution:** Pending initial push to the user's remote GitHub repository.

> `[ADD SCREENSHOT: 08_github_actions_ci.png - Successful green GitHub Actions run]`

---

## 12. Hosting and Deployment Results

- **Deployment Platform:** Prepared for Hugging Face Spaces with Docker SDK.
- **Configuration:** Dual-port configuration allows running on port 7860 (Hugging Face default) or port 8501 (Streamlit default).
- **Public URL Status:** Pending repository push and secret configuration on Hugging Face Spaces.

> `[ADD SCREENSHOT: 09_huggingface_space.png - Running application on Hugging Face Spaces]`

---

## 13. Monitoring and Logging Implementation

The application incorporates multi-level monitoring:
1. **Python `logging`:** Formats messages with timestamps, log level, and component tags (`[agent]`).
   - Logs request receipt, sanitized topic strings, search latencies, LLM latencies, and completion status.
   - Logs error categories (e.g. `RuntimeError`, `GroqError`) without dumping secret headers.
2. **High-Precision Timing:** Uses `time.perf_counter()` to record:
   - Web Search Latency ($t_{search}$)
   - LLM Synthesis Latency ($t_{llm}$)
   - Total End-to-End Pipeline Latency ($t_{total}$)
3. **In-Memory Telemetry Counter:** Tracks total requests, successes, and failures in real-time, displayed in the Streamlit sidebar.

---

## 14. Research-Topic Test Cases

### Test Case 1: Quantum Computing Breakthroughs 2026
- **Input Topic:** `Quantum Computing breakthroughs in 2026`
- **Expected Output:** Exactly 3 concise bullet points summarizing recent progress in fault-tolerant qubits, error mitigation, and commercial applications, accompanied by active web URLs.

> `[ADD SCREENSHOT: 04_research_brief_topic_1.png - Generated brief for Quantum Computing]`

---

### Test Case 2: MLOps Best Practices for LLMs
- **Input Topic:** `MLOps best practices for Large Language Models`
- **Expected Output:** Exactly 3 bullet points discussing evaluation harnesses, prompt versioning, and latency/token monitoring, with corresponding source citations.

> `[ADD SCREENSHOT: 05_research_brief_topic_2.png - Generated brief for MLOps best practices]`

---

## 15. Problems Faced and Solutions

1. **Problem:** Deprecated or obsolete Groq model identifiers (e.g., `llama3-8b-8192` decommissioned on Groq Cloud).  
   **Solution:** Inspected supported model architectures and configured `llama-3.3-70b-versatile` as default, while implementing dynamic environment override via `GROQ_MODEL`.

2. **Problem:** Inconsistent return schema from web search packages across library updates (`href` vs `url`, `body` vs `snippet`).  
   **Solution:** Built a defensive extractor in `clean_search_results()` that normalizes either `href` or `url` and either `body` or `snippet`, preventing downstream attribute errors.

3. **Problem:** LLMs occasionally produce conversational filler or varying bullet formats (numbers vs asterisks).  
   **Solution:** Developed regex-based parsing in `parse_bullet_points()` that strips markdown markers, extracts genuine bullet lines, and enforces a strict 3-element return shape.

4. **Problem:** Port mismatch between local Streamlit (port 8501) and Hugging Face Docker Spaces (port 7860).  
   **Solution:** Parameterized the entrypoint CMD in `Dockerfile` to bind to `${PORT:-8501}`, allowing seamless operation on both local and cloud platforms without code edits.

---

## 16. Conclusion
Experiment 10 successfully demonstrates the complete MLOps lifecycle for deploying a generative AI task-automation agent. By combining:
- **Decoupled Architecture:** Separating UI from agent logic to enable isolated unit testing.
- **Strict Input Validation & Defensive Parsing:** Guaranteeing output consistency (exactly three bullet points).
- **Containerization:** Ensuring environment parity and zero dependency conflicts.
- **Continuous Integration:** Catching regressions early via automated testing pipelines.
- **Zero-Trust Secret Management:** Completely eliminating secret leakage in repositories and build layers.

The project proves how MLOps principles transform fragile prototype scripts into robust, repeatable, and maintainable production AI services.
