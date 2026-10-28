"""
Core Research & Summarization Agent for Experiment 10.
Executes the pipeline: User Topic -> DuckDuckGo Search -> Result Cleaning -> Groq LLM -> 3-Point Brief.
Fully decoupled from the Streamlit UI for automated testing and standalone execution.
"""

import logging
import re
import time
from typing import Dict, Any, List, Optional, Tuple
from duckduckgo_search import DDGS
from groq import Groq, GroqError

from config import (
    get_api_key,
    get_model,
    MAX_TOPIC_LENGTH,
    MAX_SEARCH_RESULTS,
    SEARCH_TIMEOUT_SECONDS,
    GROQ_TIMEOUT_SECONDS,
)

# Configure structured logging
logger = logging.getLogger("mlops_agent")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [agent] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class AgentMetrics:
    """In-memory operational metrics for monitoring the agent process."""
    def __init__(self):
        self.total_requests: int = 0
        self.successful_requests: int = 0
        self.failed_requests: int = 0
        self.total_search_time: float = 0.0
        self.total_llm_time: float = 0.0

    def record_success(self, search_duration: float, llm_duration: float):
        self.total_requests += 1
        self.successful_requests += 1
        self.total_search_time += search_duration
        self.total_llm_time += llm_duration

    def record_failure(self):
        self.total_requests += 1
        self.failed_requests += 1

    def get_stats(self) -> Dict[str, Any]:
        avg_search = (self.total_search_time / self.successful_requests) if self.successful_requests else 0.0
        avg_llm = (self.total_llm_time / self.successful_requests) if self.successful_requests else 0.0
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "avg_search_seconds": round(avg_search, 2),
            "avg_llm_seconds": round(avg_llm, 2),
        }


# Global metrics tracker for this runtime session
metrics = AgentMetrics()


def validate_topic(topic: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate the user-supplied topic.
    Returns (is_valid, error_message).
    """
    if topic is None:
        return False, "Topic cannot be None. Please enter a valid research topic."
    
    cleaned = topic.strip()
    if not cleaned:
        return False, "Topic cannot be empty or only whitespace. Please enter a valid topic."
    
    if len(cleaned) > MAX_TOPIC_LENGTH:
        return False, f"Topic exceeds maximum allowed length of {MAX_TOPIC_LENGTH} characters (current: {len(cleaned)})."
    
    if len(cleaned) < 2:
        return False, "Topic is too short. Please enter at least 2 characters."
    
    return True, None


def clean_search_results(raw_results: Optional[List[Dict[str, Any]]]) -> List[Dict[str, str]]:
    """
    Filter, clean, and deduplicate raw search results.
    Removes items missing URLs or bodies, and removes duplicate URLs.
    """
    if not raw_results:
        return []

    cleaned: List[Dict[str, str]] = []
    seen_urls = set()

    for item in raw_results:
        if not isinstance(item, dict):
            continue

        title = str(item.get("title", "")).strip()
        # Accommodate both 'href' and 'url' keys from different DDG library versions
        url = str(item.get("href") or item.get("url") or "").strip()
        body = str(item.get("body") or item.get("snippet") or "").strip()

        # Must have a valid URL and some content
        if not url or not url.startswith(("http://", "https://")):
            continue
        if not body and not title:
            continue

        # Deduplicate by URL
        norm_url = url.rstrip("/")
        if norm_url in seen_urls:
            continue
        seen_urls.add(norm_url)

        cleaned.append({
            "title": title or "Source Link",
            "url": url,
            "body": body,
        })

    return cleaned


def fetch_duckduckgo_instant_api(topic: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Query the official DuckDuckGo Instant Answer API as a reliable fallback.
    Prevents scraper rate-limiting (HTTP 403) from breaking search functionality.
    """
    import httpx
    url = "https://api.duckduckgo.com/"
    params = {"q": topic, "format": "json", "no_html": "1", "skip_disambig": "0"}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        response = httpx.get(url, params=params, headers=headers, timeout=SEARCH_TIMEOUT_SECONDS)
        if response.status_code != 200:
            return []
        
        data = response.json()
        results = []
        
        # Primary abstract
        abstract = data.get("AbstractText", "").strip()
        abstract_url = data.get("AbstractURL", "").strip()
        heading = data.get("Heading", "").strip()
        if abstract and abstract_url:
            results.append({
                "title": heading or topic,
                "url": abstract_url,
                "body": abstract,
            })
            
        # Related topics
        related = data.get("RelatedTopics", [])
        for item in related:
            if isinstance(item, dict) and "FirstURL" in item and "Text" in item:
                results.append({
                    "title": item.get("Text", "")[:60] or "DuckDuckGo Topic",
                    "url": item["FirstURL"],
                    "body": item["Text"],
                })
            elif isinstance(item, dict) and "Topics" in item:
                for sub in item.get("Topics", []):
                    if isinstance(sub, dict) and "FirstURL" in sub and "Text" in sub:
                        results.append({
                            "title": sub.get("Text", "")[:60] or "DuckDuckGo Topic",
                            "url": sub["FirstURL"],
                            "body": sub["Text"],
                        })
            if len(results) >= max_results:
                break
                
        return clean_search_results(results[:max_results])
    except Exception as e:
        logger.debug(f"DuckDuckGo Instant API fallback error: {e}")
        return []


def search_web(topic: str, max_results: int = MAX_SEARCH_RESULTS) -> List[Dict[str, str]]:
    """
    Perform a live web search using DuckDuckGo.
    Uses DDGS news and text endpoints with resilient fallbacks to DuckDuckGo Instant API.
    Returns cleaned search results.
    """
    logger.info(f"Executing search for topic: '{topic[:50]}' (max_results={max_results})")
    raw_results = []
    
    try:
        ddgs = DDGS(timeout=int(SEARCH_TIMEOUT_SECONDS))
        # 1. Try news search
        try:
            raw_results = ddgs.news(keywords=topic, max_results=max_results)
        except Exception as ne:
            logger.debug(f"DDGS news search notice: {ne}")

        # 2. If news returned empty, try text search
        if not raw_results:
            try:
                raw_results = ddgs.text(keywords=topic, max_results=max_results)
            except Exception as te:
                logger.debug(f"DDGS text search notice: {te}")
    except Exception as e:
        logger.debug(f"DDGS initialization notice: {e}")

    cleaned = clean_search_results(raw_results)

    # 3. If DDGS returned no results or was rate-limited, use DuckDuckGo Instant API
    if not cleaned:
        logger.info(f"Using DuckDuckGo Instant API fallback for: '{topic[:50]}'")
        cleaned = fetch_duckduckgo_instant_api(topic, max_results=max_results)

    logger.info(f"Retrieved {len(cleaned)} cleaned search results")
    return cleaned


def parse_bullet_points(llm_output: str) -> List[str]:
    """
    Extract and validate exactly three bullet points from the LLM output.
    Cleans markdown bullet markers and whitespace.
    """
    if not llm_output or not llm_output.strip():
        raise ValueError("LLM returned an empty response.")

    lines = llm_output.strip().split("\n")
    raw_bullets = []

    for line in lines:
        cleaned_line = line.strip()
        # Look for typical markdown bullet or numbered list indicators
        match = re.match(r"^(?:[\*\-\•]|\d+[\.\)])\s*(.+)$", cleaned_line)
        if match:
            bullet_text = match.group(1).strip()
            if bullet_text:
                raw_bullets.append(bullet_text)

    # If markdown bullets were not explicitly matched, try non-empty lines
    if not raw_bullets:
        raw_bullets = [l.strip() for l in lines if l.strip() and not l.strip().startswith("#")]

    if not raw_bullets:
        raise ValueError("Could not parse bullet points from the model response.")

    # Normalize to exactly three bullet points
    if len(raw_bullets) >= 3:
        return raw_bullets[:3]
    
    # If the LLM returned 1 or 2 bullets, attempt sentence segmentation on the bullets
    expanded_bullets = []
    for bullet in raw_bullets:
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", bullet) if s.strip()]
        if len(sentences) > 1 and len(expanded_bullets) + len(sentences) <= 4:
            expanded_bullets.extend(sentences)
        else:
            expanded_bullets.append(bullet)

    if len(expanded_bullets) >= 3:
        return expanded_bullets[:3]

    # If still fewer than 3, return what is available padded or raise error
    if len(expanded_bullets) > 0:
        while len(expanded_bullets) < 3:
            expanded_bullets.append(f"Additional context: Refer to the provided source citations for further technical details.")
        return expanded_bullets[:3]

    raise ValueError("LLM response did not contain sufficient structured points.")


def generate_brief_with_groq(
    topic: str,
    cleaned_results: List[Dict[str, str]],
    api_key: str,
    model: str,
) -> Tuple[List[str], float]:
    """
    Send prompt to Groq Cloud LLM to summarize evidence into exactly 3 points.
    Returns (bullet_points_list, llm_duration_seconds).
    """
    start_time = time.perf_counter()

    # Build context from cleaned search results
    context_blocks = []
    for idx, item in enumerate(cleaned_results, 1):
        context_blocks.append(f"[{idx}] Title: {item['title']}\nSnippet: {item['body']}")
    context_text = "\n\n".join(context_blocks)

    system_prompt = (
        "You are an expert research analyst agent. Your task is to produce a concise, factual research brief "
        "based strictly on the provided web search excerpts. You must strictly adhere to the following rules:\n"
        "1. Provide EXACTLY THREE distinct bullet points.\n"
        "2. Each bullet point MUST begin with a hyphen (- ).\n"
        "3. Base every statement strictly on the provided excerpts; distinguish confirmed facts from uncertainty.\n"
        "4. Do NOT invent, fabricate, or assume unsupported claims.\n"
        "5. Do NOT include markdown links, URLs, intro remarks, or concluding commentary. Only output the 3 bullet points."
    )

    user_prompt = (
        f"Research Topic: {topic}\n\n"
        f"Retrieved Search Excerpts:\n{context_text}\n\n"
        "Generate the 3-bullet research brief now:"
    )

    try:
        client = Groq(api_key=api_key, timeout=GROQ_TIMEOUT_SECONDS)
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=500,
        )
        llm_duration = time.perf_counter() - start_time
        response_text = completion.choices[0].message.content or ""
        bullets = parse_bullet_points(response_text)
        return bullets, llm_duration
    except GroqError as ge:
        logger.error(f"Groq API error: {str(ge)}")
        raise RuntimeError(f"Groq API error: {str(ge)}") from ge
    except Exception as e:
        logger.error(f"LLM generation failed: {type(e).__name__} - {str(e)}")
        raise RuntimeError(f"LLM generation failed: {str(e)}") from e


def run_research_agent(
    topic: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute the full end-to-end research automation agent workflow:
    1. Validation
    2. DuckDuckGo Search
    3. Cleaning and deduplication
    4. Groq LLM Summarization
    5. Structured packaging with timing and metrics
    """
    total_start = time.perf_counter()
    sanitized_topic = (topic or "").strip()

    logger.info(f"Agent request received for topic: '{sanitized_topic[:60]}'")

    # 1. Topic validation
    is_valid, validation_error = validate_topic(sanitized_topic)
    if not is_valid:
        metrics.record_failure()
        logger.warning(f"Validation rejected topic: {validation_error}")
        return {
            "success": False,
            "topic": sanitized_topic,
            "bullet_points": [],
            "sources": [],
            "timings": {"search_seconds": 0.0, "llm_seconds": 0.0, "total_seconds": 0.0},
            "error": validation_error,
            "raw_results_count": 0,
        }

    # 2. Check API Key
    effective_api_key = get_api_key(api_key)
    if not effective_api_key:
        metrics.record_failure()
        err_msg = "Groq API key is not configured. Please supply your GROQ_API_KEY in .env or the UI."
        logger.error(err_msg)
        return {
            "success": False,
            "topic": sanitized_topic,
            "bullet_points": [],
            "sources": [],
            "timings": {"search_seconds": 0.0, "llm_seconds": 0.0, "total_seconds": 0.0},
            "error": err_msg,
            "raw_results_count": 0,
        }

    effective_model = get_model(model)

    # 3. Web Search
    search_start = time.perf_counter()
    try:
        search_results = search_web(sanitized_topic, max_results=MAX_SEARCH_RESULTS)
        search_duration = time.perf_counter() - search_start
    except Exception as e:
        metrics.record_failure()
        return {
            "success": False,
            "topic": sanitized_topic,
            "bullet_points": [],
            "sources": [],
            "timings": {"search_seconds": 0.0, "llm_seconds": 0.0, "total_seconds": time.perf_counter() - total_start},
            "error": f"Search failed: {str(e)}",
            "raw_results_count": 0,
        }

    if not search_results:
        metrics.record_failure()
        err_msg = f"No relevant web search results found for topic: '{sanitized_topic}'."
        logger.warning(err_msg)
        return {
            "success": False,
            "topic": sanitized_topic,
            "bullet_points": [],
            "sources": [],
            "timings": {"search_seconds": round(search_duration, 3), "llm_seconds": 0.0, "total_seconds": round(time.perf_counter() - total_start, 3)},
            "error": err_msg,
            "raw_results_count": 0,
        }

    # 4. Groq LLM Summarization
    try:
        bullet_points, llm_duration = generate_brief_with_groq(
            topic=sanitized_topic,
            cleaned_results=search_results,
            api_key=effective_api_key,
            model=effective_model,
        )
    except Exception as e:
        metrics.record_failure()
        return {
            "success": False,
            "topic": sanitized_topic,
            "bullet_points": [],
            "sources": [{"title": r["title"], "url": r["url"]} for r in search_results],
            "timings": {
                "search_seconds": round(search_duration, 3),
                "llm_seconds": 0.0,
                "total_seconds": round(time.perf_counter() - total_start, 3),
            },
            "error": f"LLM Brief Generation failed: {str(e)}",
            "raw_results_count": len(search_results),
        }

    total_duration = time.perf_counter() - total_start
    metrics.record_success(search_duration, llm_duration)

    logger.info(
        f"Completed research brief for '{sanitized_topic[:40]}' in {total_duration:.2f}s "
        f"(Search: {search_duration:.2f}s, LLM: {llm_duration:.2f}s)"
    )

    sources = [{"title": r["title"], "url": r["url"]} for r in search_results]

    return {
        "success": True,
        "topic": sanitized_topic,
        "bullet_points": bullet_points,
        "sources": sources,
        "timings": {
            "search_seconds": round(search_duration, 3),
            "llm_seconds": round(llm_duration, 3),
            "total_seconds": round(total_duration, 3),
        },
        "error": None,
        "raw_results_count": len(search_results),
    }
