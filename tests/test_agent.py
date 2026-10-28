"""
Automated unit tests for Experiment 10 Agent logic.
Uses mocks to ensure deterministic, zero-network, zero-cost execution.
"""

from unittest import mock
import pytest
from groq import GroqError

from agent import (
    validate_topic,
    clean_search_results,
    parse_bullet_points,
    run_research_agent,
    AgentMetrics,
)
from config import MAX_TOPIC_LENGTH


# ==============================================================================
# Topic Validation Tests
# ==============================================================================

def test_validate_topic_valid():
    """Verify valid topic strings pass validation."""
    is_valid, error = validate_topic("Machine Learning Ops")
    assert is_valid is True
    assert error is None


def test_validate_topic_empty_or_none():
    """Verify None and empty/whitespace strings fail validation."""
    is_valid, error = validate_topic(None)
    assert is_valid is False
    assert "cannot be None" in error

    is_valid, error = validate_topic("")
    assert is_valid is False
    assert "cannot be empty" in error

    is_valid, error = validate_topic("   \n\t  ")
    assert is_valid is False
    assert "cannot be empty" in error


def test_validate_topic_too_short():
    """Verify single-character inputs fail validation."""
    is_valid, error = validate_topic("a")
    assert is_valid is False
    assert "too short" in error


def test_validate_topic_excessive_length():
    """Verify topics longer than MAX_TOPIC_LENGTH fail validation."""
    long_topic = "A" * (MAX_TOPIC_LENGTH + 1)
    is_valid, error = validate_topic(long_topic)
    assert is_valid is False
    assert f"exceeds maximum allowed length of {MAX_TOPIC_LENGTH}" in error


# ==============================================================================
# Search Result Cleaning and Deduplication Tests
# ==============================================================================

def test_clean_search_results_none_and_empty():
    """Verify clean_search_results handles empty inputs safely."""
    assert clean_search_results(None) == []
    assert clean_search_results([]) == []


def test_clean_search_results_filtering():
    """Verify invalid, non-http, and empty items are discarded."""
    raw = [
        {"title": "Valid Result", "href": "https://example.com/mlops", "body": "MLOps guidelines"},
        {"title": "Invalid URL", "href": "ftp://example.com/bad", "body": "Should be ignored"},
        {"title": "", "href": "https://example.com/no-content", "body": ""},
        "not-a-dict-item",
        {"title": "Missing URL", "body": "No link"},
    ]
    cleaned = clean_search_results(raw)
    assert len(cleaned) == 1
    assert cleaned[0]["title"] == "Valid Result"
    assert cleaned[0]["url"] == "https://example.com/mlops"
    assert cleaned[0]["body"] == "MLOps guidelines"


def test_clean_search_results_deduplication():
    """Verify duplicate URLs are removed."""
    raw = [
        {"title": "Article 1", "href": "https://example.com/article", "body": "Snippet 1"},
        {"title": "Article 1 Duplicate", "href": "https://example.com/article/", "body": "Snippet 2"},
        {"title": "Article 2", "url": "https://example.com/article2", "snippet": "Snippet 3"},
    ]
    cleaned = clean_search_results(raw)
    assert len(cleaned) == 2
    assert cleaned[0]["url"] == "https://example.com/article"
    assert cleaned[1]["url"] == "https://example.com/article2"


# ==============================================================================
# Bullet Point Parsing Tests
# ==============================================================================

def test_parse_bullet_points_standard_three():
    """Verify standard three markdown bullets are cleanly parsed."""
    llm_output = (
        "- Point 1: MLOps standardizes machine learning lifecycle.\n"
        "- Point 2: Continuous Integration verifies reproducible builds.\n"
        "- Point 3: Containerization guarantees environment parity."
    )
    bullets = parse_bullet_points(llm_output)
    assert len(bullets) == 3
    assert bullets[0].startswith("Point 1")
    assert bullets[1].startswith("Point 2")
    assert bullets[2].startswith("Point 3")


def test_parse_bullet_points_numbered_list():
    """Verify numbered list format is parsed into clean bullets."""
    llm_output = (
        "1. First breakthrough in deep learning.\n"
        "2. Second breakthrough in model distillation.\n"
        "3. Third breakthrough in agentic reasoning."
    )
    bullets = parse_bullet_points(llm_output)
    assert len(bullets) == 3
    assert "First breakthrough" in bullets[0]
    assert "Second breakthrough" in bullets[1]
    assert "Third breakthrough" in bullets[2]


def test_parse_bullet_points_more_than_three():
    """Verify when LLM returns >3 points, exactly the first 3 are selected."""
    llm_output = "\n".join([f"- Point {i}" for i in range(1, 6)])
    bullets = parse_bullet_points(llm_output)
    assert len(bullets) == 3
    assert bullets == ["Point 1", "Point 2", "Point 3"]


def test_parse_bullet_points_fewer_than_three():
    """Verify when LLM returns fewer points, exactly 3 points are formatted."""
    llm_output = "- Point 1: Comprehensive overview of automated agents."
    bullets = parse_bullet_points(llm_output)
    assert len(bullets) == 3
    assert "Point 1" in bullets[0]


def test_parse_bullet_points_empty():
    """Verify empty response raises ValueError."""
    with pytest.raises(ValueError, match="empty response"):
        parse_bullet_points("")
    with pytest.raises(ValueError, match="empty response"):
        parse_bullet_points("   \n  ")


# ==============================================================================
# End-to-End Pipeline Mocked Tests
# ==============================================================================

def test_run_research_agent_missing_api_key():
    """Verify missing API key returns a clear error without crashing."""
    with mock.patch("agent.get_api_key", return_value=None):
        result = run_research_agent("Artificial Intelligence")
        assert result["success"] is False
        assert "Groq API key is not configured" in result["error"]
        assert result["bullet_points"] == []


def test_run_research_agent_invalid_topic():
    """Verify invalid topic returns validation failure."""
    result = run_research_agent("")
    assert result["success"] is False
    assert "cannot be empty" in result["error"]


@mock.patch("agent.search_web")
def test_run_research_agent_no_search_results(mock_search):
    """Verify handling when search returns 0 results."""
    mock_search.return_value = []
    result = run_research_agent("ObscureQuery123456789", api_key="gsk_mock_valid_key_123456")
    assert result["success"] is False
    assert "No relevant web search results found" in result["error"]


@mock.patch("agent.search_web")
def test_run_research_agent_search_failure(mock_search):
    """Verify handling when search raises an exception (e.g. network error)."""
    mock_search.side_effect = RuntimeError("DuckDuckGo rate limit reached")
    result = run_research_agent("Testing Search Error", api_key="gsk_mock_valid_key_123456")
    assert result["success"] is False
    assert "Search failed: Web search error" in result["error"] or "Search failed" in result["error"]


@mock.patch("agent.generate_brief_with_groq")
@mock.patch("agent.search_web")
def test_run_research_agent_llm_failure(mock_search, mock_groq):
    """Verify handling when Groq LLM API request fails."""
    mock_search.return_value = [
        {"title": "Test Title", "url": "https://example.com/test", "body": "Test Snippet"}
    ]
    mock_groq.side_effect = RuntimeError("Groq Cloud 503 Service Unavailable")
    result = run_research_agent("Testing LLM Error", api_key="gsk_mock_valid_key_123456")
    assert result["success"] is False
    assert "LLM Brief Generation failed" in result["error"]


@mock.patch("agent.generate_brief_with_groq")
@mock.patch("agent.search_web")
def test_run_research_agent_success(mock_search, mock_groq):
    """Verify complete successful pipeline flow returns 3 bullets, sources, and metrics."""
    mock_search.return_value = [
        {"title": "Source 1", "url": "https://example.com/1", "body": "Snippet 1"},
        {"title": "Source 2", "url": "https://example.com/2", "body": "Snippet 2"},
    ]
    mock_groq.return_value = (
        ["Bullet 1: Fact", "Bullet 2: Discovery", "Bullet 3: Conclusion"],
        0.42,  # llm_seconds
    )

    result = run_research_agent("MLOps Automation", api_key="gsk_mock_valid_key_123456")

    assert result["success"] is True
    assert result["error"] is None
    assert len(result["bullet_points"]) == 3
    assert result["bullet_points"][0] == "Bullet 1: Fact"
    assert len(result["sources"]) == 2
    assert result["sources"][0]["url"] == "https://example.com/1"
    assert result["timings"]["total_seconds"] >= 0
    assert result["timings"]["llm_seconds"] == 0.42


# ==============================================================================
# Operational Metrics Tests
# ==============================================================================

def test_agent_metrics_tracking():
    """Verify in-memory metrics record success and failure accurately."""
    m = AgentMetrics()
    assert m.total_requests == 0
    assert m.successful_requests == 0
    assert m.failed_requests == 0

    m.record_success(0.5, 1.2)
    m.record_failure()

    stats = m.get_stats()
    assert stats["total_requests"] == 2
    assert stats["successful_requests"] == 1
    assert stats["failed_requests"] == 1
    assert stats["avg_search_seconds"] == 0.5
    assert stats["avg_llm_seconds"] == 1.2
