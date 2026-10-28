# Practical Submission Screenshot Checklist — Experiment 10

This checklist guides you through capturing authentic verification screenshots for your college laboratory submission for **Experiment 10: MLOps Deployment of a Task-Automation Agent**.

> **Note:** Never submit fabricated or placeholder images. Follow the instructions below to capture real screenshots from your local environment or deployment.

---

## 📸 Checklist of Required Screenshots

| # | Screenshot Identifier | What to Capture | Purpose & What It Proves |
|---|---|---|---|
| **1** | `01_env_and_git_status.png` | PowerShell terminal showing `python --version`, `git status`, and `.gitignore` file contents. | Proves clean local repository setup and that `.env` is properly ignored to prevent credential leakage. |
| **2** | `02_pytest_passing.png` | PowerShell terminal running `.\.venv\Scripts\python.exe -m pytest` with all 27 tests passing. | Proves automated unit testing, input validation, and robust exception handling. |
| **3** | `03_app_ui_initial.png` | Browser at `http://localhost:8501` showing the Streamlit application interface, topic input field, and sidebar status. | Proves functional web UI and non-leaking configuration status indicator. |
| **4** | `04_research_brief_topic_1.png` | Browser showing completed research brief for **Example Topic 1** with exactly 3 bullet points, source links, and processing metrics. | Proves live end-to-end web search and Groq LLM synthesis pipeline. |
| **5** | `05_research_brief_topic_2.png` | Browser showing completed research brief for **Example Topic 2** with 3 distinct bullets and corresponding citations. | Proves agent generalization across different technical domains. |
| **6** | `06_session_history_sidebar.png` | Sidebar showing updated telemetry metrics (Total Requests = 2, Success = 2, latencies) and expanded history. | Proves logging, performance monitoring, and in-memory session persistence. |
| **7** | `07_docker_build_and_run.png` | PowerShell terminal showing `docker build` command and container running on port 8501. *(If Docker Desktop is running)* | Proves containerization and non-root execution. |
| **8** | `08_github_actions_ci.png` | GitHub repository `Actions` tab showing the green checkmark for the CI workflow run. | Proves automated Continuous Integration pipeline. |
| **9** | `09_huggingface_space.png` | Hugging Face Spaces interface showing the running Docker Space and live public URL. *(If deployed to cloud)* | Proves Continuous Deployment to a cloud platform. |

---

## 🧪 Instructions to Capture Example Topic Outputs

### Example Topic 1:
**Input Topic:** `Quantum Computing breakthroughs in 2026`
- **Steps:**
  1. Ensure your Groq API key is present in `.env` or pasted in the sidebar password field.
  2. Enter `Quantum Computing breakthroughs in 2026` in the text field.
  3. Click **🚀 Generate Research Brief**.
  4. Wait for the loading spinner to complete.
  5. Verify that exactly three bullet points appear under **📋 3-Point Research Brief**.
  6. Verify that the **🔗 Cited Web Sources** section displays clickable hyperlinks.
  7. Capture screenshot `04_research_brief_topic_1.png`.

---

### Example Topic 2:
**Input Topic:** `MLOps best practices for Large Language Models`
- **Steps:**
  1. Enter `MLOps best practices for Large Language Models` in the text field.
  2. Click **🚀 Generate Research Brief**.
  3. Verify that the new research brief displays 3 fresh bullet points tailored to MLOps for LLMs.
  4. Verify that latency badges show Search Latency, LLM Latency, and Total Duration.
  5. Expand the **📜 Session Search History** dropdown at the bottom of the page to confirm both searches are preserved.
  6. Capture screenshot `05_research_brief_topic_2.png`.

---

## 🛡️ Pre-Submission Verification Safeguards
Before taking screenshots:
- [ ] Confirm no API key is visible in any terminal window or browser tab.
- [ ] Confirm the sidebar displays masked credentials (e.g. `gsk_...xyz`).
- [ ] Confirm the research brief contains **exactly three** numbered or bulleted points.
