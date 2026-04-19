import os
import chromadb
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate

from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain

# Load environment variables from the local .env file on your Mac
load_dotenv()

def initialize_cinema_brain():
    """Sets up the connection to ChromaDB and initializes the AI reasoning chain."""

    # 1. Connect to ChromaDB
    chroma_host = os.getenv("CHROMA_HOST", "10.0.0.2")
    chroma_port = int(os.getenv("CHROMA_PORT", 8000))

    remote_client = chromadb.HttpClient(host=chroma_host, port=chroma_port)

    # 2. Setup the Embedding Function
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

    # 3. Connect to the existing vector store collection
    vectorstore = Chroma(
        client=remote_client,
        collection_name="indie_movies",
        embedding_function=embeddings
    )

    # 4. Initialize the Reasoning Model
    llm = ChatGoogleGenerativeAI(model="models/gemini-2.5-flash", temperature=0.1)

    # 5. Define the System Prompt
    system_prompt = (
        "You are Cinema Scout, an expert AI assistant specializing in independent cinema, "
        "film festivals, and realistic dramas. "
        "Use the following pieces of retrieved context to answer the user's question. "
        "If the answer is not contained within the context, explicitly state that you do not know. "
        "Keep your answers insightful, concise, and focused on the provided reviews.\n\n"
        "When asked about movies, you must extract and provide specific film titles from the context. If no specific titles are mentioned in the context, explicitly say 'I cannot find a specific title in the database.'"
        "Context:\n{context}"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}")
    ])

    # 6. Create the Document Chain (Combines the retrieved chunks)
    document_chain = create_stuff_documents_chain(llm, prompt)

    # 6. Create the Document Chain (Combines the retrieved chunks)
    document_chain = create_stuff_documents_chain(llm, prompt)

    # 7. Create the Retrieval Chain (Handles the search and generation loop)
    # k=5 means it will fetch the top 5 most relevant review chunks from the Pi
    retriever = vectorstore.as_retriever(search_kwargs={"k": 15})
    rag_chain = create_retrieval_chain(retriever, document_chain)

    return rag_chain


def ask_cinema_scout(query: str):
    """Executes a query against the vector database and prints the result."""
    print(f"\n[Cinema Scout] Searching the Pi database for: '{query}'...")

    try:
        brain = initialize_cinema_brain()
        response = brain.invoke({"input": query})

        print("\n" + "*" * 40)
        print("RESPONSE:")
        print("*" * 40)
        print(response["answer"])
        print("*" * 40 + "\n")

    except Exception as e:
        print(f"\n[Error] Failed to execute query. Details: {e}")

if __name__ == "__main__":
    if not os.getenv("GOOGLE_API_KEY"):
        print("[Error] GOOGLE_API_KEY is missing. Please add it to your .env file.")
        exit(1)

    # Execute a test query
    test_question = "What is the best festival award winning realistic drama in the last 5 years"
    ask_cinema_scout(test_question)

