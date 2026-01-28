import sys
import os
import asyncio
from dotenv import load_dotenv

# Add src to python path
sys.path.append(os.path.join(os.getcwd(), "src"))

# Load env vars
load_dotenv()

from core import extractor

async def test_url():
    url = "https://cyberlaw.stanford.edu/publications/how-ai-destroys-institutions/"
    print(f"Testing URL: {url}")
    
    try:
        article, fallback, error = await extractor.scrape_article(url)
        
        if error:
            print(f"Extraction failed with error: {error}")
        elif article:
            print(f"Extraction successful!")
            print(f"Title: {article.title}")
            print(f"Text length: {len(article.text)}")
            print(f"Tags: {article.tags}")
        else:
            print("Extraction returned None with no error message.")
            
    except Exception as e:
        print(f"CRASH during extraction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_url())
