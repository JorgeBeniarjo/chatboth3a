import os
import httpx
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Global in-memory knowledge base
_knowledge_base = ""

async def load_kb_from_github() -> bool:
    """
    Downloads the knowledge base from a raw GitHub Markdown URL.
    The URL is set via the KB_URL environment variable.
    Returns True on success, False on failure.
    """
    global _knowledge_base

    kb_url = os.getenv("KB_URL", "")
    if not kb_url:
        logger.warning("KB_URL not set. Knowledge base not loaded.")
        return False

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            logger.info(f"Loading knowledge base from: {kb_url}")
            response = await client.get(kb_url, timeout=15.0)
            response.raise_for_status()
            _knowledge_base = response.text
            logger.info(f"Knowledge base loaded successfully. Size: {len(_knowledge_base)} chars.")
            return True
    except Exception as e:
        logger.error(f"Error loading knowledge base from GitHub: {e}")
        return False


def get_knowledge_base() -> str:
    """Returns the current in-memory knowledge base."""
    return _knowledge_base
