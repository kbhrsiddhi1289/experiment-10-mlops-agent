"""
Configuration management for Experiment 10: Task Automation Agent.
Safely handles environment variables, configuration defaults, and status inspection
without exposing sensitive credentials.
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load local environment variables from .env file if present
load_dotenv()

# Default configuration parameters
APP_VERSION = "1.1.0"
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
DEFAULT_PORT = 8501
MAX_TOPIC_LENGTH = 300
MAX_SEARCH_RESULTS = 5
SEARCH_TIMEOUT_SECONDS = 15.0
GROQ_TIMEOUT_SECONDS = 30.0


def get_api_key(override_key: Optional[str] = None) -> Optional[str]:
    """
    Retrieve the Groq API key from explicit override or environment variable.
    Returns None if empty or not configured.
    """
    if override_key and override_key.strip():
        return override_key.strip()
    env_key = os.getenv("GROQ_API_KEY", "").strip()
    return env_key if env_key else None


def get_model(override_model: Optional[str] = None) -> str:
    """
    Retrieve the configured Groq model ID, falling back to default.
    """
    if override_model and override_model.strip():
        return override_model.strip()
    return os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL).strip() or DEFAULT_GROQ_MODEL


def get_server_port() -> int:
    """
    Retrieve application server port (useful for Hugging Face Spaces vs local dev).
    """
    port_str = os.getenv("PORT", str(DEFAULT_PORT)).strip()
    try:
        return int(port_str)
    except ValueError:
        return DEFAULT_PORT


def is_api_key_configured(override_key: Optional[str] = None) -> bool:
    """
    Check if a valid non-empty API key is available without revealing it.
    """
    key = get_api_key(override_key)
    return bool(key and len(key) >= 10)


def mask_api_key(key: Optional[str]) -> str:
    """
    Safely mask an API key for status display (e.g. gsk_...xyz).
    Never returns full secret.
    """
    if not key:
        return "Not Set"
    key_str = key.strip()
    if len(key_str) <= 8:
        return "***"
    return f"{key_str[:4]}...{key_str[-4:]}"


def get_system_status(override_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Return sanitized system configuration status for UI and monitoring.
    Never exposes raw secrets.
    """
    key = get_api_key(override_key)
    return {
        "app_version": APP_VERSION,
        "search_provider": "DuckDuckGo (Live Web)",
        "search_status": "Ready",
        "llm_provider": "Groq Cloud",
        "llm_model": get_model(),
        "api_key_configured": bool(key),
        "api_key_masked": mask_api_key(key),
        "port": get_server_port(),
        "max_results": MAX_SEARCH_RESULTS,
    }
