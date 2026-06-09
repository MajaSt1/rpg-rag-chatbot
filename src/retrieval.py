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


def search(query: str, n_results: int = 3) -> list[str]:
    """Zwraca top-N fragmentów pasujących do pytania."""
    results = collection.query(query_texts=[query], n_results=n_results)
    
    documents = results["documents"][0]
    distances = results["distances"][0]
    metadatas = results["metadatas"][0] 

    for i in range(len(documents)):
        sekcja = metadatas[i].get('section', 'Brak')
        plik = metadatas[i].get('source', 'Brak')



    return documents


if __name__ == "__main__":
    load_documents()
    print("Baza wiedzy gotowa.")