# /Users/nickfox137/Documents/llm-creative-studio/python/config.py
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# LLM Models
CHATGPT_MODEL = "gpt-3.5-turbo"
GEMINI_MODEL = "gemini-1.5-flash"
CLAUDE_MODEL = "claude-3-haiku-20240307"

# Data Paths
DATA_DIR = "data"  # Relative to the project root
METADATA_FILE = "data/metadata.json"
