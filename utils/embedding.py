# utils/embedding.py

import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

# Load .env if needed
load_dotenv()

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
