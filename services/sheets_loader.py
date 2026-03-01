import os
import csv
import httpx
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variable to store the in-memory context from the spreadsheets
_knowledge_base = ""

async def load_csv_data():
    """
    Downloads and parses CSV data from the URLs specified in the .env file.
    The data is kept in memory. Files are parsed using ';' as a delimiter.
    """
    global _knowledge_base
    csv_urls_str = os.getenv("CSV_URLS", "")
    if not csv_urls_str:
        logger.warning("No CSV_URLS specified in .env.")
        return

    urls = [url.strip() for url in csv_urls_str.split(",") if url.strip()]
    
    extracted_text = []

    async with httpx.AsyncClient(follow_redirects=True) as client:
        for i, url in enumerate(urls):
            try:
                logger.info(f"Loading CSV from URL {i+1}...")
                response = await client.get(url, timeout=15.0)
                response.raise_for_status()
                
                # The text is decoded as utf-8
                text_content = response.text
                
                # Parse with csv module (Google Sheets uses ',' by default)
                reader = csv.reader(text_content.splitlines(), delimiter=',')
                
                extracted_text.append(f"--- Documento Operativo {i+1} ---")
                for row in reader:
                    # Filter out purely empty columns
                    cleaned_row = [cell.strip() for cell in row if cell.strip()]
                    if cleaned_row:
                        extracted_text.append(" | ".join(cleaned_row))
                        
            except Exception as e:
                logger.error(f"Error loading CSV from {url}: {e}")
                
    _knowledge_base = "\n".join(extracted_text)
    logger.info(f"Knowledge base in-memory successfully updated. Total lines extracted: {len(extracted_text)}")

def get_knowledge_base() -> str:
    """Returns the current loaded knowledge base as a single string."""
    return _knowledge_base
