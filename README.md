# Cinema Scout

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688)
![Streamlit](https://img.shields.io/badge/Streamlit-1.25+-FF4B4B)
![LangChain](https://img.shields.io/badge/LangChain-Integration-green)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)

**Cinema Scout** is an autonomous, Agentic AI media assistant designed to bridge the gap between film discovery and automated homelab media management. By combining Retrieval-Augmented Generation (RAG) with local services like [Seerr](https://seerr.dev/), [Radarr](https://radarr.video/), and [Sonarr](https://sonarr.tv/), it acts as both a knowledgeable film critic and an automated media requester.

## Motivation

Film enthusiasts often rely on specialized RSS feeds (like IndieWire or Roger Ebert) to discover award-winning, independent, or foreign films. However, moving from discovery to acquisition requires manually cross-referencing titles, logging into local media request servers, searching for the film, and requesting it. 

Cinema Scout automates this entire pipeline. Using a LangChain-powered conversational agent, users can ask for recommendations based on recent reviews, and seamlessly instruct the agent to securely search and request the film directly to their local media server in a single conversation.

## Architecture

The project is built on a decoupled microservices architecture. The system boundaries span from the user-facing chat interface down to the local media ecosystem.

1. **Chat UI (Streamlit):** A lightweight, user-friendly conversational frontend. It acts as the sole user endpoint, interacting strictly over HTTP with the Agent API.
2. **Agent API (FastAPI):** A stateless REST API hosting the LangChain Agent. It serves as the core reasoning engine, taking user inputs, querying the vector database for context, and executing tool calls.
3. **ChromaDB (Vector Database):** A centralized vector store hosting semantic embeddings of film reviews and articles.
4. **Ingestion Worker:** A headless background service that polls RSS feeds, sanitizes HTML payloads, embeds the text, and stores it in ChromaDB to keep the agent's knowledge base fresh.
5. **Seerr Integration:** The final boundary. The agent maps the requested title to the local media ecosystem via Seerr, validates the TMDB ID, and submits a precise request.

### The Agentic Flow

The core of Cinema Scout is an intelligent routing loop managed by LangChain. It determines exactly when to rely on its training data, when to search the local database, and when to execute external commands:

1. **User Request:** A user submits a query through the Streamlit Chat UI.
2. **LangChain Orchestration:** The FastAPI backend receives the prompt and passes it to the initialized agent.
3. **LLM Evaluation:** The LLM evaluates the prompt's intent. 
4. **RAG and Semantic Search:** If the user asks for recommendations, asks about a specific indie film, or seeks context not widely known, the LLM determines it needs external knowledge. It formulates a query and triggers a semantic search against ChromaDB. The database returns the most relevant review excerpts.
5. **Contextual Synthesis:** The LLM injects the retrieved RSS data into its context window, generating an informed, up-to-date response.
6. **Action Execution:** If the user explicitly asks to "download" or "request" a film, the LLM bypasses the database search entirely. It directly triggers the Seerr integration tools, mapping the parsed title to a TMDB ID, and posting the request to the media server.

### Architecture Component Diagram

The following diagram illustrates the decoupled microservices architecture of Cinema Scout, mapping the precise, hub-and-spoke sequential workflow from the initial chat interface, through the core agent and RAG components, down to the final Seerr integration boundary. 

![Architecture Component Diagram](./docs/architecture-diagram.png)

## Data Modeling (ChromaDB)

The vector database is optimized for semantic retrieval of film critiques and context.

* **Collection Name:** indie_movies
* **Vector Dimensions:** 768 (via Embeddings Model)
* **Payload structure:**
    * **page_content:** Cleaned, plain-text extraction of RSS article summaries.
    * **metadata:**
        * **title** (string): The title of the article/review.
        * **source** (string): The canonical URL of the article, enabling the agent to provide factual citations.
* **Retrieval Strategy:** Top-K semantic search (k=15) to ensure adequate context window coverage for surrounding movie titles and director names.

## Ingestion and RSS Feed Management

The knowledge base of Cinema Scout is entirely driven by the RSS feeds configured in the ingestion worker. Adding new feeds expands the agent's contextual awareness, allowing it to recommend and discuss a wider variety of genres or localized content.

To add or modify the sources the agent reads:
1. Open `app/ingest.py`.
2. Locate the `RSS_FEEDS` list.
3. Add the feed URL of your desired publication (e.g., a horror movie blog or a specific festival's news feed).
4. Restart the `ingestion-worker` container. The worker will automatically poll the new feed, embed the articles, and store them in ChromaDB on its next scheduled run.

## Configuration

System configuration is managed via Environment Variables. These are securely injected via the `.env` file and `docker-compose.yml`.

| Variable | Description |
| :--- | :--- |
| `GOOGLE_API_KEY` | Your Gemini API key for LLM and Embeddings. |
| `SEERR_URL` | The internal network URL to your Seerr instance (e.g., `http://seerr:5055` or `http://10.0.0.x:5055`). |
| `SEERR_API_KEY` | Authentication token generated from your Seerr UI. |
| `CHROMA_HOST` | Hostname for the vector DB (defaults to `chromadb` in Docker). |
| `CHROMA_PORT` | Port for the vector DB (defaults to `8000`). |
| `LANGCHAIN_API_KEY` | (Optional) Enables LangSmith tracing for agent observability. |

## Build and Installation

This project utilizes standard Docker Compose for orchestration, making it agnostic to your host OS. Ensure Docker and Docker Compose are installed on your target machine.

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/cinema-scout.git
   cd cinema-scout
   ```
2. Create your `.env` file in the root directory and populate it with the variables listed in the Configuration section.

## Deployment

Deployment is handled entirely through Docker Compose. The configuration builds the necessary images and wires the internal network routing.

```bash
docker compose up -d --build
```

### Accessing the Services
* **Chat UI:** `http://localhost:8501` (or your server's IP)
* **Agent API Docs:** `http://localhost:8000/docs`

## API Documentation

The decoupled Agent API exposes a standard REST endpoint for executing the LangChain agent.

### POST /chat
Executes the agent's reasoning loop and returns a sanitized text response.

**Request Body:**
```json
{
  "input": "I'm looking for the Italian film 'Five Seconds' from 2025. Please request it."
}
```

**Response:**
```json
{
  "output": "I have successfully found 'Cinque Secondi' (2025) in your Seerr database and submitted a request. Radarr is now monitoring it for a release."
}
```

## Future Improvements

* **Model Context Protocol (MCP) Integration:** Refactor custom Seerr tools into a standardized MCP server to allow interoperability with other generic AI agents.
* **TV Show Expansion:** Add logic and endpoints to support Sonarr integration for episodic content.
* **Enhanced RAG Pipelines:** Implement a hybrid search (Keyword BM25 + Semantic) to better capture exact movie title matches in dense review articles.
* **Authentication:** Add a basic Auth middleware to the Streamlit UI to expose it safely outside the local subnet.
