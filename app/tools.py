import os
import requests
import urllib.parse
from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()

@tool
def search_seerr_movies(title: str) -> str:
    """
    Use this tool FIRST when a user wants to request a movie.
    It searches Seerr and returns a list of matches with their TMDB IDs, release years, and original languages.
    """
    seerr_url = os.getenv("SEERR_URL", "").rstrip("/")
    api_key = os.getenv("SEERR_API_KEY")
    headers = {"X-Api-Key": api_key, "Accept": "application/json"}

    encoded_title = urllib.parse.quote(title)
    search_endpoint = f"{seerr_url}/api/v1/search?query={encoded_title}"

    response = requests.get(search_endpoint, headers=headers)
    if response.status_code != 200:
        return f"Error connecting to Seerr Search API: {response.status_code}"

    results = response.json().get("results", [])
    if not results:
        return f"No movies found for '{title}'."

    output = []
    # Grab the top 5 results so the LLM has options to evaluate
    for item in results[:5]:
        if item.get("mediaType") == "movie":
            m_id = item.get("id")
            m_title = item.get("title", "Unknown")
            m_year = item.get("releaseDate", "Unknown")[:4]  # Extract just the YYYY
            m_lang = item.get("originalLanguage", "Unknown")
            m_overview = item.get("overview", "No description.")[:100]
            output.append(f"ID: {m_id} | Title: {m_title} | Year: {m_year} | Lang: {m_lang} | Plot: {m_overview}...")

    if not output:
        return f"No valid movie formats found for '{title}'."

    return "\n".join(output)


@tool
def request_movie_by_id(tmdb_id: int) -> str:
    """
    Use this tool SECOND to actually request the movie on Seerr.
    Pass the exact TMDB ID (integer) identified from the search_seerr_movies tool.
    """
    seerr_url = os.getenv("SEERR_URL", "").rstrip("/")
    api_key = os.getenv("SEERR_API_KEY")

    request_endpoint = f"{seerr_url}/api/v1/request"
    post_headers = {"X-Api-Key": api_key, "Content-Type": "application/json"}
    payload = {
        "mediaId": tmdb_id,
        "mediaType": "movie"
    }

    req_response = requests.post(request_endpoint, json=payload, headers=post_headers)

    if req_response.status_code in [200, 201]:
        return f"Successfully requested TMDB ID: {tmdb_id}."
    elif req_response.status_code == 409:
        return f"Movie ID {tmdb_id} has already been requested or is available."
    else:
        return f"Failed to request ID {tmdb_id}. Status: {req_response.status_code}"