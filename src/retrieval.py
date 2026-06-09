"""
Osoba 1 — baza wiedzy: ładowanie dokumentów, chunking semantyczny, embeddingi, wyszukiwanie.
"""

import os
import re
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()

CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "rpg_knowledge"

openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.getenv("OPENAI_API_KEY"),
    model_name="text-embedding-3-small"
)

client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=openai_ef
)


def parse_text_semantically(text: str, file_name: str) -> tuple[list[str], list[dict]]:
    """
    Dzieli tekst na podstawie separatorów === NAGŁÓWEK ===.
    Zwraca listę chunków oraz odpowiadającą im listę metadanych (source i section).
    """
    chunks = []
    metadatas = []
    
    parts = re.split(r'===\s*(.*?)\s*===', text)
    
    if parts[0].strip():
        chunks.append(f"Źródło: {file_name}\nSekcja: Wstęp\n{parts[0].strip()}")
        metadatas.append({"source": file_name, "section": "Wstęp"})
        
    for i in range(1, len(parts), 2):
        section_name = parts[i].strip()
        content = parts[i+1].strip() if i+1 < len(parts) else ""
        
        if content:
            chunk_text = f"Źródło: {file_name}\nSekcja: {section_name}\n{content}"
            chunks.append(chunk_text)
            
            metadatas.append({
                "source": file_name, 
                "section": section_name
            })
            
    return chunks, metadatas


def load_documents(data_dir: str = "data") -> None:
    """Wczytuje wszystkie .txt z folderu data/ i dodaje do ChromaDB."""
    files = list(Path(data_dir).glob("*.txt"))
    if not files:
        print(f"Brak plików .txt w {data_dir}/")
        return

    for file in files:
        text = file.read_text(encoding="utf-8")
        
        chunks, metadatas = parse_text_semantically(text, file.name)
        
        if not chunks:
            continue
            
        ids = [f"{file.stem}_{i}" for i in range(len(chunks))]

        collection.upsert(documents=chunks, ids=ids, metadatas=metadatas)
        print(f"Załadowano {file.name}: {len(chunks)} chunków semantycznych")


# Parametry wyszukiwania (patrz SPRAWOZDANIE.md, sekcja o ograniczeniach RAG).
# Zamiast pobierać stałą liczbę fragmentów, filtrujemy je progiem podobieństwa —
# dzięki temu liczba zwracanych fragmentów dopasowuje się do pytania:
# wąskie pytanie dostaje 2-3 trafne, szerokie kilkanaście.
SIMILARITY_THRESHOLD = 0.47  # podobieństwo = 1 - odległość kosinusowa
CANDIDATE_POOL = 15          # ile kandydatów rozważamy przed filtrowaniem
MIN_RESULTS = 2              # bezpiecznik: zawsze zwróć przynajmniej tyle


def list_documents(data_dir: str = "data") -> list[str]:
    """Zwraca nazwy plików .txt dostępnych w bazie wiedzy."""
    return sorted(p.name for p in Path(data_dir).glob("*.txt"))


def get_full_document(filename: str, data_dir: str = "data") -> str:
    """
    Zwraca CAŁĄ treść jednego dokumentu z bazy.
    Używane w trybie agregacji (routing) — gdy pytanie wymaga kompletu danych,
    np. "która klasa ma najwięcej HP?" potrzebuje wszystkich klas naraz.
    """
    path = Path(data_dir) / filename
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def search(query: str, threshold: float = SIMILARITY_THRESHOLD) -> list[str]:
    """
    Zwraca fragmenty, których podobieństwo do pytania przekracza próg.
    Pobieramy pulę kandydatów, a następnie odrzucamy te poniżej progu.
    Jeśli żaden nie przekroczy progu, zwracamy MIN_RESULTS najlepszych
    (lepiej dać modelowi słaby kontekst niż pusty).
    """
    results = collection.query(
        query_texts=[query],
        n_results=CANDIDATE_POOL,
        include=["documents", "distances"],
    )
    documents = results["documents"][0]
    distances = results["distances"][0]

    kept = [
        doc for doc, dist in zip(documents, distances)
        if (1 - dist) >= threshold
    ]

    # Bezpiecznik: nigdy nie zwracaj pustej listy.
    if len(kept) < MIN_RESULTS:
        return documents[:MIN_RESULTS]
    return kept


if __name__ == "__main__":
    load_documents()
    print("Baza wiedzy gotowa.")