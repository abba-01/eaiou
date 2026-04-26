"""
eaiou agent team — configuration
All credentials loaded from environment.
"""
import os
from dotenv import load_dotenv

# Load /scratch/repos/eaiou/.env if present (dev). Production uses server env.
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"), override=False)
# Also load root .env for ANTHROPIC_API_KEY
load_dotenv(dotenv_path="/root/.env", override=False)

BASE_URL: str = os.getenv("EAIOU_BASE_URL", "https://eaiou.org")

# nginx invite gate
NGINX_USER: str = os.getenv("EAIOU_NGINX_USER", "invited")
NGINX_PASS: str = os.getenv("EAIOU_NGINX_PASS", "n1YsmGN0lLrrUqpdaSSmg")

# eaiou admin session login
ADMIN_USER: str = os.getenv("EAIOU_ADMIN_USER", "mae")
ADMIN_PASS: str = os.getenv("EAIOU_ADMIN_PASS", "Wcv3sM60NPNfhRYQO0ZxYtK0Yw1!")

# Anthropic
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

# Paper generation
PAPER_TOPIC: str = os.getenv(
    "PAPER_TOPIC",
    "The role of sleep architecture in memory consolidation during adolescence",
)
AUTHOR_NAME: str = os.getenv("AUTHOR_NAME", "Dr. A. Synthesis")
AUTHOR_ORCID: str = os.getenv("AUTHOR_ORCID", "0009-0000-0000-0001")

# Models
MODEL_CONTENT: str = "claude-sonnet-4-6"   # author content generation
MODEL_MIRA: str    = "claude-sonnet-4-6"   # mira's module_id in eaiou system
