import os
import chromadb
from dotenv import load_dotenv

# LangChain Core and Agent Imports
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.tools import create_retriever_tool
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

# Import the decoupled Seerr tools
from app.tools import search_seerr_movies, request_movie_by_id

# 1. Load Environment Variables
load_dotenv()


def get_cinema_scout_agent():
    """Initializes and returns the autonomous LangChain agent."""

    # 2. Connect to the ChromaDB Container
    chroma_host = os.getenv("CHROMA_HOST", "chromadb")
    chroma_port = int(os.getenv("CHROMA_PORT", 8000))
    remote_client = chromadb.HttpClient(host=chroma_host, port=chroma_port)

    # 3. Setup Embedding and Database Retriever
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    vectorstore = Chroma(
        client=remote_client,
        collection_name="indie_movies",
        embedding_function=embeddings
    )

    # We use k=15 to ensure we capture the movie titles in the surrounding text
    retriever = vectorstore.as_retriever(search_kwargs={"k": 15})

    # 4. Create the Retriever Tool
    retriever_tool = create_retriever_tool(
        retriever,
        "search_movie_reviews",
        "Search for movie reviews, festival winners, realistic dramas, and cinematic analysis. Use this first to find specific movie titles and recommendations."
    )

    # 5. Define the Agent's Toolset
    tools = [retriever_tool, search_seerr_movies, request_movie_by_id]

    # 6. Initialize the LLM Reasoning Engine
    llm = ChatGoogleGenerativeAI(model="models/gemini-2.5-flash", temperature=0.1)

    # 7. Create the Agent Prompt with the new SOP
    system_prompt = (
        "You are Cinema Scout, a professional film critic and assistant. "
        "When asked for a recommendation, always use the search_movie_reviews tool to find options from your database. "
        "When asked to request or download a movie, you must follow a strict two step process: "
        "1. Always use the search_seerr_movies tool first to get a list of matching titles. "
        "2. Analyze the results against the user's constraints (e.g., release year, language, director). "
        "3. Once you identify the exact correct match, use the request_movie_by_id tool with that specific ID. "
        "Do not guess the ID and do not skip the search step. Be concise and professional."
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    # 8. Assemble the Agent Executor
    agent = create_tool_calling_agent(llm, tools, prompt)

    # Setting verbose=True allows us to watch the agent's thought process
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    return agent_executor


if __name__ == "__main__":
    # Local Testing Block
    if not os.getenv("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY is missing in .env")
        exit(1)

    print("Initializing Cinema Scout Agent...")
    scout = get_cinema_scout_agent()

    # Test the new decoupled logic with specific constraints
    test_query = "Do not search the database. Just use your tools to request the Italian movie 'Five Seconds' from 2025 on Seerr."
    print(f"\nUser Query: {test_query}\n")

    try:
        # Trigger the Agent
        response = scout.invoke({"input": test_query})
        print("\nFinal Output:")
        print(response["output"])
    except Exception as e:
        print(f"Agent execution failed: {e}")