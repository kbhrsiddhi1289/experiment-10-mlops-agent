# ==============================================================================
# Windows PowerShell Startup Script for Experiment 10
# Never put real API credentials inside this script.
# ==============================================================================

param(
    [string]$Command = "app"
)

$VenvPython = ".\.venv\Scripts\python.exe"
$VenvStreamlit = ".\.venv\Scripts\streamlit.exe"
$VenvPytest = ".\.venv\Scripts\pytest.exe"

function Show-Help {
    Write-Host "==========================================================" -ForegroundColor Cyan
    Write-Host " Experiment 10: Task Automation Agent (MLOps)" -ForegroundColor Cyan
    Write-Host "==========================================================" -ForegroundColor Cyan
    Write-Host "Usage:"
    Write-Host "  .\run.ps1 app      - Run the Streamlit web application"
    Write-Host "  .\run.ps1 test     - Run automated pytest unit test suite"
    Write-Host "  .\run.ps1 docker   - Build and run the local Docker container"
    Write-Host "  .\run.ps1 setup    - Create virtual environment and install dependencies"
    Write-Host "=========================================================="
}

if (-not (Test-Path $VenvPython) -and ($Command -ne "setup")) {
    Write-Host "[WARNING] Virtual environment not found at .\.venv" -ForegroundColor Yellow
    Write-Host "Running setup first..." -ForegroundColor Cyan
    python -m venv .venv
    .\.venv\Scripts\python.exe -m pip install --upgrade pip
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt
}

switch ($Command.ToLower()) {
    "app" {
        Write-Host "[INFO] Starting Streamlit App on http://localhost:8501 ..." -ForegroundColor Green
        & $VenvPython -m streamlit run app.py --server.port 8501
    }
    "test" {
        Write-Host "[INFO] Running automated test suite with pytest..." -ForegroundColor Green
        & $VenvPython -m pytest -v
    }
    "docker" {
        Write-Host "[INFO] Checking Docker..." -ForegroundColor Cyan
        if (-not (Test-Path ".env")) {
            Write-Host "[NOTE] .env file not found. Remember to copy .env.example to .env and set your GROQ_API_KEY." -ForegroundColor Yellow
        }
        Write-Host "[INFO] Building Docker image: experiment-10-agent:local ..." -ForegroundColor Green
        docker build -t experiment-10-agent:local .
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[INFO] Running Docker container on http://localhost:8501 ..." -ForegroundColor Green
            docker run --rm -p 8501:8501 --env-file .env experiment-10-agent:local
        } else {
            Write-Host "[ERROR] Docker build failed. Please ensure Docker Desktop is running." -ForegroundColor Red
        }
    }
    "setup" {
        Write-Host "[INFO] Setting up virtual environment and dependencies..." -ForegroundColor Green
        python -m venv .venv
        & $VenvPython -m pip install --upgrade pip
        & $VenvPython -m pip install -r requirements.txt
        Write-Host "[SUCCESS] Setup complete. Copy .env.example to .env and add your GROQ_API_KEY." -ForegroundColor Green
    }
    default {
        Show-Help
    }
}
