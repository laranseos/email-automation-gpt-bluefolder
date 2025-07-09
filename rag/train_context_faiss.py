import argparse
import os
import sys
import shutil
import base64
from pathlib import Path
from typing import List
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'services')))

from gmail_auth import get_gmail_service

# Load environment variables
print("[INFO] Loading environment variables...")
load_dotenv()

# Constants
DB_PATH = "faiss_index"
DATA_FOLDER = "data"
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def fetch_replies(service) -> List[Document]:
    print("[INFO] Fetching replies from Gmail...")
    results = service.users().messages().list(userId='me', q="in:sent").execute()
    messages = results.get('messages', [])
    print(f"[DEBUG] Total sent messages fetched: {len(messages)}")

    documents = []

    for message in messages:
        msg = service.users().messages().get(userId='me', id=message['id']).execute()
        payload = msg.get('payload', {})
        headers = payload.get('headers', [])

        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
        sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')

        parts = payload.get('parts', [])
        body = ''
        if parts:
            for part in parts:
                if part.get('mimeType') == 'text/plain':
                    try:
                        body = base64.urlsafe_b64decode(part.get('body', {}).get('data', '')).decode('utf-8')
                    except Exception as e:
                        print(f"[ERROR] Failed to decode body for message {message['id']}: {e}")
                    break
        else:
            body = msg.get('snippet', '')

        documents.append(Document(
            page_content=body,
            metadata={
                "subject": subject,
                "sender": sender,
                "email_id": message['id']
            }
        ))

    print(f"[INFO] Total email documents created: {len(documents)}")
    return documents


def load_documents_from_directory(directory: str) -> List[Document]:
    print(f"[INFO] Loading documents from: {directory}")
    documents = []

    for file_path in Path(directory).rglob('*'):
        try:
            if file_path.suffix == ".pdf":
                print(f"[DEBUG] Loading PDF: {file_path}")
                loader = PyPDFLoader(str(file_path))
                documents.extend(loader.load())
            elif file_path.suffix == ".docx":
                print(f"[DEBUG] Loading DOCX: {file_path}")
                loader = Docx2txtLoader(str(file_path))
                documents.extend(loader.load())
            elif file_path.suffix == ".txt":
                print(f"[DEBUG] Loading TXT: {file_path}")
                loader = TextLoader(str(file_path))
                documents.extend(loader.load())
            else:
                print(f"[WARN] Skipping unsupported file: {file_path}")
        except Exception as e:
            print(f"[ERROR] Failed to load {file_path}: {e}")

    print(f"[INFO] Total documents loaded from directory: {len(documents)}")
    return documents


def split_documents(documents: List[Document]) -> List[Document]:
    print(f"[INFO] Splitting {len(documents)} documents into chunks...")
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=80)
    chunks = splitter.split_documents(documents)
    print(f"[INFO] Total chunks created: {len(chunks)}")
    return chunks


def calculate_chunk_ids(chunks: List[Document]) -> List[Document]:
    print("[INFO] Calculating unique chunk IDs...")
    source_chunk_count = {}
    for chunk in chunks:
        source = chunk.metadata.get("source", "unknown")
        index = source_chunk_count.get(source, 0)
        chunk.metadata["id"] = f"{source}:{index}"
        source_chunk_count[source] = index + 1
    print("[INFO] Chunk ID assignment completed.")
    return chunks


def get_embedding_function():
    print("[INFO] Initializing OpenAI embedding function...")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("[FATAL] OPENAI_API_KEY is missing. Set it in a .env file or environment variable.")

    print("[SUCCESS] ✅ OpenAI API Key loaded.")
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=openai_api_key
    )


def add_to_vectorstore(chunks: List[Document]):
    print(f"[INFO] Preparing to add chunks to FAISS vectorstore at '{DB_PATH}'...")
    embedding_fn = get_embedding_function()

    chunks = calculate_chunk_ids(chunks)

    db = None
    existing_ids = set()

    if os.path.exists(DB_PATH):
        print("[DEBUG] Loading existing FAISS index...")
        db = FAISS.load_local(DB_PATH, embeddings=embedding_fn, allow_dangerous_deserialization=True)
        existing_ids = set(d.metadata.get("id") for d in db.docstore._dict.values())
    else:
        print("[DEBUG] No existing FAISS index found. It will be created only if new chunks are found.")

    new_chunks = [chunk for chunk in chunks if chunk.metadata["id"] not in existing_ids]
    print(f"[INFO] New chunks to be added: {len(new_chunks)}")

    if new_chunks:
        if db is None:
            db = FAISS.from_documents(new_chunks, embedding=embedding_fn)
        else:
            db.add_documents(new_chunks)

        db.save_local(DB_PATH)
        print(f"[SUCCESS] ✅ {len(new_chunks)} new chunks added and saved to FAISS.")
    else:
        print("[INFO] No new chunks to add.")


def clear_database():
    if os.path.exists(DB_PATH):
        shutil.rmtree(DB_PATH)
        print("[INFO] Database cleared.")
    else:
        print("[INFO] No database found to clear.")


def main():
    parser = argparse.ArgumentParser(description="Process and manage email + file data.")
    parser.add_argument("--reset", action="store_true", help="Reset the FAISS vector store.")
    args = parser.parse_args()

    if args.reset:
        clear_database()

    print("[STEP 1] Loading local documents...")
    file_documents = load_documents_from_directory(DATA_FOLDER)

    print("[STEP 2] Authenticating and loading email replies...")
    service = get_gmail_service()
    email_documents = fetch_replies(service)

    print("[STEP 3] Combining and splitting documents...")
    all_docs = file_documents + email_documents
    chunks = split_documents(all_docs)

    print("[STEP 4] Embedding and storing in FAISS...")
    add_to_vectorstore(chunks)

    print("[DONE] ✅ All documents processed and added to vector store.")


if __name__ == "__main__":
    main()
