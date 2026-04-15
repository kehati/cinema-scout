import os
import feedparser
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import chromadb

# 1. Load Environment Variables (.env file)
load_dotenv()

CHROMA_HOST = os.getenv("CHROMA_HOST", "10.0.0.2")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", 8000))
COLLECTION_NAME = "indie_movies"

if "GOOGLE_API_KEY" not in os.environ:
    raise ValueError("Missing GOOGLE_API_KEY environment variable. Check your .env file.")

RSS_FEEDS = [
    "https://www.indiewire.com/c/film/reviews/feed/",
    "https://letterboxd.com/journal/rss/"
]

# 2. Initialize the Google Embedding Model (Updated to the current V1 model)
embedding_function = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

# 3. Connect to the ChromaDB Thin Client
print(f"Connecting to ChromaDB at {CHROMA_HOST}:{CHROMA_PORT}...")
chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)


def fetch_and_process_feeds():
    documents = []
    metadatas = []
    ids = []

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

    # --- DELTA INGESTION LOGIC ---
    # Fetch existing links to prevent duplicate embedding costs
    print("Fetching existing database records...")
    existing_data = collection.get(include=["metadatas"])
    seen_links = set()

    if existing_data and existing_data["metadatas"]:
        for meta in existing_data["metadatas"]:
            if meta and "link" in meta:
                seen_links.add(meta["link"])

    print(f"Database currently holds {len(seen_links)} unique articles.")
    print("Checking RSS feeds for new content...\n")

    # --- FETCH AND CHUNK NEW FEEDS ---
    for feed_url in RSS_FEEDS:
        print(f"Polling: {feed_url}")
        feed = feedparser.parse(feed_url)
        new_entries_count = 0

        for entry in feed.entries:
            link = entry.get('link', '')

            # Skip if already in the database
            if link in seen_links:
                continue

            title = entry.get('title', 'Unknown Title')
            summary = entry.get('summary', '')

            # Combine for rich vector context
            full_text = f"Title: {title}\n\nReview: {summary}"
            chunks = text_splitter.split_text(full_text)

            for i, chunk in enumerate(chunks):
                chunk_id = f"{link}_chunk_{i}"

                documents.append(chunk)
                metadatas.append({"title": title, "source": feed_url, "link": link})
                ids.append(chunk_id)

            new_entries_count += 1
            seen_links.add(link)  # Add to seen links so we don't process duplicates within the same run

        print(f"  -> Found {new_entries_count} new articles.")

    # --- EMBED AND STORE ---
    if documents:
        print(f"\nSending {len(documents)} new text chunks to Google for vectorization...")
        embeddings = embedding_function.embed_documents(documents)

        print("Saving to ChromaDB...")
        collection.upsert(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print("Ingestion complete. Database is up to date!")
    else:
        print("\nNo new articles found. Database is up to date!")


if __name__ == "__main__":
    fetch_and_process_feeds()