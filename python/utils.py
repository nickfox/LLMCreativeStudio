# /Users/nickfox137/Documents/llm-creative-studio/python/utils.py
import logging

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
