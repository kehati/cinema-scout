# Cinema Scout: System Context

## Project Overview
Cinema Scout is a decoupled, agentic RAG system that automates the discovery and acquisition of independent and international cinema. It reads RSS feeds of film reviews, processes semantic searches, and interacts with local homelab APIs (Seerr, Radarr) to fulfill user requests. The system's curation logic must always prioritize cinematic and artistic quality over technical quality or streaming availability when generating film lists.

## Architecture Boundaries
1. Client Tier: Streamlit chat UI. Strictly visual and conversational. No direct database access.
2. AI Platform: FastAPI backend orchestrating LangChain. This acts as the sole brain of the application. It routes queries to the vector database or directly to external tool calls based on user intent.
3. Knowledge Base: Background Python worker located in the `app/` directory. Polls RSS feeds, cleans HTML, generates embeddings using `gemini-embedding-001`, and stores them in ChromaDB.
4. Action Tier: Seerr API. The agent must resolve movie requests to a specific TMDB ID before executing the HTTP tool call to Seerr.

## Tech Stack
* Language: Python 3.11+
* Package Management: `uv` (utilizing `pyproject.toml` and `uv.lock`, with an exported `requirements.txt`)
* Web Frameworks: FastAPI (Backend), Streamlit (Frontend)
* AI/Agent Orchestration: LangChain
* LLM: Google `gemini-2.5-flash`
* Vector Database: ChromaDB
* Infrastructure: Docker (via `Dockerfile`)

## Repository Structure
* `app/`: Contains the core application code, including the FastAPI backend and ingestion worker.
* `docs/`: Hosts project documentation and architecture diagrams.
* `check_models.py`: Utility script for validating model availability and API connections.
* `pyproject.toml` / `uv.lock`: Primary dependency management configuration.

## Data Models
ChromaDB Collection: indie_movies
Payload Structure:
* `page_content`: Plain text of the review.
* `metadata`:
  * `title`: String.
  * `source`: String (URL).

## Development Conventions
* Strict type hinting is required for all Python functions.
* Asynchronous execution must be used for all I/O bound tasks, especially external API calls to Seerr or ChromaDB.
* Do not hallucinate dependencies. Stick to the established tech stack and manage dependencies via `uv`.
* Future integrations will include Model Context Protocol (MCP) servers and Sonarr endpoints.