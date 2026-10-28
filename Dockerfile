# ==============================================================================
# Dockerfile for Experiment 10: Task Automation Agent
# Compatible with both Local Docker (port 8501) and Hugging Face Spaces (port 7860)
# ==============================================================================

FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PORT=8501

# Set workspace directory
WORKDIR /app

# Install system dependencies if required
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a secure non-root user with UID 1000 (standard for Hugging Face Spaces)
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app /home/appuser/.streamlit && \
    chown -R appuser:appuser /app /home/appuser

# Install Python dependencies first for caching efficiency
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY --chown=appuser:appuser config.py .
COPY --chown=appuser:appuser agent.py .
COPY --chown=appuser:appuser app.py .

# Switch to non-root user
USER appuser

# Expose ports: 8501 (Local Development default) and 7860 (Hugging Face Spaces default)
EXPOSE 8501
EXPOSE 7860

# Predictable healthcheck to verify Streamlit server responsiveness
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl --fail http://localhost:${PORT:-8501}/_stcore/health || exit 1

# Launch Streamlit with configurable port and headless settings
CMD ["sh", "-c", "streamlit run app.py --server.port=${PORT:-8501} --server.address=0.0.0.0 --server.headless=true --browser.gatherUsageStats=false"]
