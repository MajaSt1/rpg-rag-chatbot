"""Uruchom ten skrypt raz, żeby załadować dokumenty do bazy."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from retrieval import load_documents

load_documents(data_dir="data")
