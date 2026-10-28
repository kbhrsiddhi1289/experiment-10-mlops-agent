"""
Automated unit tests for configuration and secret management.
Verifies safe environment handling, key masking, and port configuration.
"""

import os
from unittest import mock
import pytest

from config import (
    get_api_key,
    get_model,
    get_server_port,
    is_api_key_configured,
    mask_api_key,
    get_system_status,
    DEFAULT_GROQ_MODEL,
    DEFAULT_PORT,
)


def test_get_api_key_with_override():
    """Verify explicit override takes precedence over environment variable."""
    with mock.patch.dict(os.environ, {"GROQ_API_KEY": "env_secret_key"}):
        assert get_api_key("override_key_123") == "override_key_123"


def test_get_api_key_from_env():
    """Verify loading API key from environment when no override is given."""
    with mock.patch.dict(os.environ, {"GROQ_API_KEY": "gsk_test_mock_key_999"}):
        assert get_api_key() == "gsk_test_mock_key_999"


def test_get_api_key_empty():
    """Verify None is returned when key is not set or empty."""
    with mock.patch.dict(os.environ, {"GROQ_API_KEY": ""}):
        assert get_api_key() is None
        assert get_api_key("   ") is None


def test_get_model_default_and_override():
    """Verify model selection defaults and override mechanisms."""
    with mock.patch.dict(os.environ, {}, clear=True):
        assert get_model() == DEFAULT_GROQ_MODEL
        assert get_model("llama-3.1-8b-instant") == "llama-3.1-8b-instant"

    with mock.patch.dict(os.environ, {"GROQ_MODEL": "custom-groq-model"}):
        assert get_model() == "custom-groq-model"
        assert get_model("priority-model") == "priority-model"


def test_get_server_port():
    """Verify port configuration and fallback for invalid values."""
    with mock.patch.dict(os.environ, {"PORT": "7860"}):
        assert get_server_port() == 7860

    with mock.patch.dict(os.environ, {"PORT": "invalid_port"}):
        assert get_server_port() == DEFAULT_PORT

    with mock.patch.dict(os.environ, {}, clear=True):
        assert get_server_port() == DEFAULT_PORT


def test_is_api_key_configured():
    """Verify API key existence checking."""
    assert is_api_key_configured(None) is False
    assert is_api_key_configured("") is False
    assert is_api_key_configured("short") is False
    assert is_api_key_configured("gsk_valid_length_key_12345") is True


def test_mask_api_key():
    """Verify masking never returns raw credentials and handles edge cases."""
    assert mask_api_key(None) == "Not Set"
    assert mask_api_key("") == "Not Set"
    assert mask_api_key("1234") == "***"
    
    masked = mask_api_key("gsk_sample_secret_key_8899")
    assert masked.startswith("gsk_")
    assert masked.endswith("8899")
    assert "sample_secret" not in masked
    assert "..." in masked


def test_get_system_status():
    """Verify status dictionary contains expected fields and masks keys."""
    status = get_system_status("gsk_mock_secure_key_1122")
    assert status["search_provider"] == "DuckDuckGo (Live Web)"
    assert status["llm_provider"] == "Groq Cloud"
    assert status["api_key_configured"] is True
    assert status["api_key_masked"].startswith("gsk_")
    assert "mock_secure" not in status["api_key_masked"]
    assert "port" in status
