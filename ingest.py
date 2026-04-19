import os
import time
import logging
import feedparser
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
import chromadb

# Set up standard logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load local environment variables (if running on Mac for testing)
load_dotenv()

# The Professional Indie Cinema Feeds
RSS_FEEDS = [
    "https://www.indiewire.com/c/criticism/feed/",
    "https://www.rogerebert.com/feed"
]


def initialize_vectorstore():
    """Connects to ChromaDB and sets up the embedding model."""
    chroma_host = os.getenv("CHROMA_HOST", "chromadb")
    chroma_port = int(os.getenv("CHROMA_PORT", 8000))

    logger.info(f"Connecting to ChromaDB at {chroma_host}:{chroma_port}")
    remote_client = chromadb.HttpClient(host=chroma_host, port=chroma_port)

    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

    vectorstore = Chroma(
        client=remote_client,
        collection_name="indie_movies",
        embedding_function=embeddings
    )
    return vectorstore


def fetch_and_process_feeds(vectorstore):
    """Fetches RSS feeds, cleans HTML, and stores them with metadata."""
    logger.info("Starting ingestion cycle...")

    for feed_url in RSS_FEEDS:
        logger.info(f"Fetching feed: {feed_url}")
        parsed_feed = feedparser.parse(feed_url)

        for entry in parsed_feed.entries:
            try:
                # 1. Extract raw data
                title = entry.get('title', 'Unknown Title')
                link = entry.get('link', '')
                raw_summary = entry.get('summary', '')

                # Skip entries with no content or missing links
                if not raw_summary or not link:
                    continue

                # Chroma returns a dictionary. If the 'ids' list has items, it exists.
                existing_doc = vectorstore.get(ids=[link])
                if existing_doc and len(existing_doc['ids']) > 0:
                    logger.debug(f"Skipping already ingested entry: {title}")
                    continue

                # 3. Clean the HTML using BeautifulSoup
                soup = BeautifulSoup(raw_summary, "html.parser")
                clean_text = soup.get_text(separator=" ", strip=True)

                # 4. Create the Metadata Dictionary
                metadata = {
                    "title": title,
                    "source": link
                }

                # 5. Save to ChromaDB
                vectorstore.add_texts(
                    texts=[clean_text],
                    metadatas=[metadata],
                    ids=[link]
                )
                logger.info(f"Successfully ingested: {title}")

            except Exception as e:
                logger.error(f"Error processing entry '{title}': {e}")

    logger.info("Ingestion cycle complete.")

if __name__ == "__main__":
    # Ensure GOOGLE_API_KEY is available
    if not os.getenv("GOOGLE_API_KEY"):
        logger.error("GOOGLE_API_KEY is missing. Exiting.")
        exit(1)

    try:
        db = initialize_vectorstore()
    except Exception as e:
        logger.error(f"Failed to connect to ChromaDB: {e}")
        exit(1)

    # The Infinite Loop for Docker
    while True:
        try:
            fetch_and_process_feeds(db)
        except Exception as e:
            logger.error(f"Unexpected error during ingestion: {e}")

        logger.info("Sleeping for 1 hour...")
        time.sleep(3600)