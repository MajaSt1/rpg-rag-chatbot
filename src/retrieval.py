"""
Osoba 1 — baza wiedzy: ładowanie dokumentów, chunking, embeddingi, wyszukiwanie.
"""

import os
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()

CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "rpg_knowledge"
CHUNK_SIZE = 400  # znaki
CHUNK_OVERLAP = 50

openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.getenv("OPENAI_API_KEY"),
    model_name="text-embedding-3-small"
)

client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=openai_ef
)


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


def load_documents(data_dir: str = "data") -> None:
    """Wczytuje wszystkie .txt z folderu data/ i dodaje do ChromaDB."""
    files = list(Path(data_dir).glob("*.txt"))
    if not files:
        print(f"Brak plików .txt w {data_dir}/")
        return

    for file in files:
        text = file.read_text(encoding="utf-8")
        chunks = chunk_text(text)
        ids = [f"{file.stem}_{i}" for i in range(len(chunks))]
        metadatas = [{"source": file.name} for _ in chunks]

        collection.upsert(documents=chunks, ids=ids, metadatas=metadatas)
        print(f"Załadowano {file.name}: {len(chunks)} chunków")


def search(query: str, n_results: int = 3) -> list[str]:
    """Zwraca top-N fragmentów pasujących do pytania."""
    results = collection.query(query_texts=[query], n_results=n_results)
    return results["documents"][0]


if __name__ == "__main__":
    load_documents()
    print("Baza wiedzy gotowa.")
