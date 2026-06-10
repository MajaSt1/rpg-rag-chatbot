# RPG RAG Chatbot

Asystent do gier fabularnych (RPG) oparty na RAG (Retrieval-Augmented Generation).
Projekt na zaliczenie przedmiotu Systemy Dialogowe.

## Jak działa?

```
Pytanie użytkownika
    ↓
Wyszukiwanie w bazie wiedzy (ChromaDB + embeddingi)
    ↓
Top-3 fragmenty jako kontekst
    ↓
GPT-4o-mini generuje odpowiedź na podstawie kontekstu
```

## Struktura projektu

```
rpg-rag-chatbot/
├── data/               # dokumenty .txt z wiedzą o RPG
├── src/
│   ├── retrieval.py    # ładowanie dokumentów, embeddingi, wyszukiwanie
│   ├── chatbot.py      # logika rozmowy, integracja OpenAI
│   └── ui.py           # interfejs Gradio
├── scripts/
│   └── load_data.py    # skrypt do załadowania bazy wiedzy
├── requirements.txt
└── .env.example
```

## Uruchomienie

1. Sklonuj repo i wejdź do folderu:
```bash
git clone <url>
cd rpg-rag-chatbot
```

2. Zainstaluj zależności:
```bash
pip install -r requirements.txt
```

3. Stwórz plik `.env`:
```bash
cp .env.example .env
# wpisz swój klucz OpenAI w .env
```

4. Załaduj bazę wiedzy (raz):
```bash
python scripts/load_data.py
```

5. Uruchom chatbota:
```bash
# CLI
python src/chatbot.py

# Interfejs Gradio
python src/ui.py
```

## Przykładowe zapytania

```
user: która klasa ma najwięcej HP?
assistant: Klasa z największą ilością punktów życia w Dungeons & Dragons 5. edycji
to Barbarzyńca, który ma 1d12 punktów życia na poziom.

user: która klasa współgra z rasą krasnoluda?
assistant: Klasa, która szczególnie dobrze współgra z rasą krasnoluda, to Barbarzyńca,
ze względu na ich wysoką Kondycję i odporność na obrażenia. Inne klasy, które również
mogą dobrze pasować, to Wojownik i Paladyn, które korzystają z wysokiej wytrzymałości
i umiejętności walki. Krasnoludowie są znani z miłości do walki i honoru, co czyni je
idealnymi dla klas frontowych.

user: ile jest ras?
assistant: W Dungeons & Dragons 5. edycji jest 13 ras, które zostały wymienione
w dostarczonym kontekście.

user: która klasa ma najmniej HP?
assistant: Klasa z najmniejszą ilością punktów życia w Dungeons & Dragons 5. edycji
to Czarodziej, który ma 1d6 punktów życia na poziom.

user: pojedyncze fakty + pizza
assistant: Nie mam tej informacji w bazie wiedzy.
```

## Podział pracy

| Osoba | Zakres |
|---|---|
| Osoba 1 | `data/`, `src/retrieval.py` — baza wiedzy, chunking, embeddingi |
| Osoba 2 | `src/chatbot.py`, `src/ui.py` — logika chatbota, UI |
