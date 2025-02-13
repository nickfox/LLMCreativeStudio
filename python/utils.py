# /Users/nickfox137/Documents/llm-creative-studio/python/utils.py
import logging

# --- Simple In-Memory Cache ---  (Moved from main.py)
cache = {}  # {prompt: {"response": response_text, "llm": llm_name}}

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

def get_cached_response(cache_key: str):
    """Retrieves a cached response if it exists."""
    if cache_key in cache:
        logging.info(f"Cache hit for key: {cache_key}")
        return cache[cache_key]
    return None

def store_cached_response(cache_key: str, response_data: dict):
    """Stores a response in the cache."""
    cache[cache_key] = response_data
