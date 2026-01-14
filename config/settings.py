"""Settings and environment variable management."""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# SQL Agent Config
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
SQL_TIMEOUT_SECONDS = int(os.getenv("SQL_TIMEOUT_SECONDS", "30"))

# LangChain Configuration
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
LANGCHAIN_ENDPOINT = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY", "")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "ai-assistant")

# LLM Configuration
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_TEMPERATURE_SQL = float(os.getenv("LLM_TEMPERATURE_SQL", "0.1"))
LLM_TEMPERATURE_RESPONSE = float(os.getenv("LLM_TEMPERATURE_RESPONSE", "0.7"))
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "30"))
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "2"))

# Memory Configuration
MEMORY_WINDOW_SIZE = int(os.getenv("MEMORY_WINDOW_SIZE", "3"))

# Natural Language Generation Config
NLG_ENABLED = os.getenv("NLG_ENABLED", "true").lower() == "true"
NLG_MAX_ROWS = int(os.getenv("NLG_MAX_ROWS", "10"))  # Max rows to include in prompt

# Company ID (default for testing)
DEFAULT_COMPANY_ID = 29447