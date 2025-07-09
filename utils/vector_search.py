# utils/vector_search.py

from typing import List
from langchain.schema import Document
from langchain_chroma import Chroma
import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

load_dotenv()

CHROMA_PATH = "../rag/chroma_db"  # Adjust if needed

def get_embedding_function():
    """
    Returns the OpenAI embedding function used throughout the RAG system.
    """
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not openai_api_key:
        raise ValueError("[FATAL] OPENAI_API_KEY is missing. Set it in .env or environment variable.")

    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=openai_api_key
    )


def search_vector_store(query: str, num_results: int = 3, similarity_threshold: float = 0.7) -> List[Document]:
    """
    Connect to Chroma vector store and return documents similar to the query above a threshold.
    """
    print("\n[DEBUG] Initializing Chroma vector store...")

    try:
        db = Chroma(persist_directory=CHROMA_PATH, embedding_function=get_embedding_function())
        count = len(db.get()["ids"])
        if count == 0:
            print(f"[WARN] Chroma loaded but has no documents: {CHROMA_PATH}")
        else:
            print(f"[SUCCESS] Chroma loaded from {CHROMA_PATH} with {count} documents.")
    except Exception as e:
        print(f"[ERROR] Failed to load Chroma DB: {e}")
        return []

    print(f"[INFO] Running similarity search with threshold: {similarity_threshold}")
    
    try:
        results = db.similarity_search_with_score(query, k=num_results)
    except Exception as e:
        print(f"[ERROR] Similarity search failed: {e}")
        return []

    relevant_documents = []

    for idx, (doc, score) in enumerate(results):

        if score >= similarity_threshold:
            relevant_documents.append(doc)

    print(f"\n[INFO] Relevant documents returned: {len(relevant_documents)}")
    return relevant_documents
