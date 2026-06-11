"""
Osoba 2 — logika chatbota: integracja OpenAI, retrieval, historia rozmowy.
"""

import os
import re
from openai import OpenAI
from dotenv import load_dotenv
from retrieval import search, list_documents, get_full_document

# Siatka bezpieczeństwa dla routingu: słowa-sygnały typowe dla pytań agregujących.
# Wykrywają TYLKO, że pytanie jest agregujące — nie wskazują pliku (ten ustala się
# z metadanych najlepszego trafienia retrievalu). Dzięki temu działa dla każdego
# tematu, a nie tylko dla z góry wpisanych plików.
AGGREGATION_SIGNALS = (
    "najwięcej", "najmniej", "najwyższ", "najniższ", "najlepsz", "najgorsz",
    "najsilniejsz", "najsłabsz", "najtwardsz", "wszystkie", "wszystkich",
    "ile jest", "która z", "które z", "porównaj", "porównanie", "wypisz", "lista",
)

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """Jesteś pomocnym asystentem i ekspertem od gier RPG.
Twoim głównym zadaniem jest odpowiadanie na pytania użytkownika WYŁĄCZNIE w oparciu o dostarczony poniżej "Kontekst z bazy wiedzy".

ZASADY:
1. ELASTYCZNOŚĆ POJĘĆ: Bądź domyślny. Jeśli użytkownik pyta o "postacie", a w kontekście masz "klasy postaci" lub "rasy", załóż, że o to pyta i udziel odpowiedzi.
2. CZĘŚCIOWE DOPASOWANIE: Jeśli pytanie jest ogólne, a w bazie masz powiązane informacje, użyj ich. (np. "W bazie nie mam konkretnych bohaterów, ale mogę opowiedzieć Ci o klasach postaci, takich jak...").
3. ZAKAZ ZMYŚLANIA: Nigdy nie wymyślaj własnych statystyk, zasad ani mechanik, których nie ma w Kontekście.
4. BRAK WIEDZY: Dopiero gdy Kontekst absolutnie w 100% nie dotyczy zadanego pytania, odpowiedz: "Nie mam tej informacji w bazie wiedzy."
5. FORMAT: Odpowiadaj naturalnie, krótko i po polsku."""


def classify_query(user_question: str, force: bool = False) -> list[str]:
    """
    Routing: rozpoznaje pytania AGREGUJĄCE (porównujące/zliczające wiele obiektów,
    np. "która klasa ma najwięcej HP?", "ile jest ras?") oraz pytania ŁĄCZĄCE TEMATY
    (np. "która klasa najlepiej współgra z rasą krasnoluda?").

    Takie pytania wymagają KOMPLETU danych, a wyszukiwanie po podobieństwie zwraca
    tylko podzbiór fragmentów. Dlatego pytamy tani model, które dokumenty z bazy
    wczytać w CAŁOŚCI. Model NIE generuje tu odpowiedzi — jedynie wybiera ścieżkę.

    force=True wyłącza opcję "NONE" — używane przez siatkę bezpieczeństwa, gdy słowa-
    sygnały wskazują pytanie agregujące, a zwykła klasyfikacja je przeoczyła.

    Zwraca listę nazw plików do wczytania w całości (może być kilka dla pytań
    łączących tematy) albo pustą listę (wtedy używamy zwykłego RAG).
    """
    docs = list_documents()
    none_clause = (
        "Pytanie NA PEWNO jest agregujące — MUSISZ wskazać co najmniej jeden plik, "
        "nie wolno Ci odpowiedzieć NONE."
        if force else
        "Zwykłe pytanie o jeden konkretny fakt (np. 'ile HP ma Wojownik') "
        "NIE jest agregujące — wtedy odpowiedz: NONE."
    )
    decision = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": (
                "Oceń, czy pytanie użytkownika jest AGREGUJĄCE. Pytanie jest agregujące, gdy:\n"
                "- porównuje lub zestawia WIELE elementów w obrębie jednego tematu "
                "(np. 'która z wszystkich klas ma najwięcej/najmniej HP', 'ile jest ras', "
                "'wypisz wszystkie zaklęcia') → wskaż JEDEN plik;\n"
                "- ŁĄCZY różne tematy (np. 'która klasa najlepiej współgra z rasą "
                "krasnoluda') → wskaż KILKA plików.\n"
                f"{none_clause}\n\n"
                f"Dostępne dokumenty bazy wiedzy: {', '.join(docs)}\n\n"
                f"Pytanie: {user_question}\n\n"
                "Wypisz nazwy WSZYSTKICH potrzebnych plików z listy, oddzielone "
                "przecinkami (zwykle 1, ale dla pytań łączących tematy kilka), "
                "albo NONE. Nie dodawaj nic więcej."
            ),
        }],
        max_tokens=60,
        temperature=0,
    )
    answer = decision.choices[0].message.content.strip()
    # Parsujemy listę nazw plików, zachowując tylko te faktycznie istniejące w bazie.
    names = [name.strip() for name in answer.split(",")]
    return [name for name in names if name in docs]


def build_prompt(user_question: str) -> tuple[str, int, list[str]]:
    target_docs = classify_query(user_question)
    if not target_docs and any(s in user_question.lower() for s in AGGREGATION_SIGNALS):
        # Siatka bezpieczeństwa: słowa-sygnały wskazują pytanie agregujące, którego
        # klasyfikator nie złapał. Ponawiamy klasyfikację z wymuszeniem wyboru pliku
        # (ten sam mechanizm wyboru, ale bez opcji rezygnacji) — pewniejsze niż
        # zgadywanie pliku z retrievalu, który mógłby trafić w zły dokument.
        target_docs = classify_query(user_question, force=True)

    sources = []
    fragments_count = 0

    if target_docs:
        # Tryb agregacji: całe dokumenty zamiast fragmentów (komplet danych).
        # Dla pytań łączących tematy może to być kilka plików naraz.
        context = "\n\n---\n\n".join(get_full_document(doc) for doc in target_docs)
        sources = target_docs
        fragments_count = len(target_docs)  # W trybie agregacji traktujemy każdy pełny plik jako 1 duży fragment
    else:
        # Zwykły RAG: fragmenty pasujące do pytania.
        fragments = search(user_question)
        context = "\n\n---\n\n".join(fragments)
        fragments_count = len(fragments)
        
        # Ekstrakcja nazw plików z metadanych ("Źródło: nazwa.txt") z tekstów chunków
        for frag in fragments:
            match = re.search(r"Źródło:\s*(.*)", frag)
            if match:
                src = match.group(1).strip()
                if src not in sources:
                    sources.append(src)

    prompt = f"Kontekst z bazy wiedzy:\n{context}\n\nPytanie: {user_question}"
    return prompt, fragments_count, sources


def chat(history: list[dict], user_message: str) -> tuple[str, list[dict], int, list[str]]:
    """Wysyła wiadomość i zwraca odpowiedź + zaktualizowaną historię + statystyki retrievalu."""
    augmented, frag_count, sources = build_prompt(user_message)
    
    api_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *history,
        {"role": "user", "content": augmented},
    ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=api_messages,
        max_tokens=512,
        temperature=0.3,
    )

    reply = response.choices[0].message.content
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": reply})
    
    return reply, history, frag_count, sources


if __name__ == "__main__":
    print("RPG Asystent gotowy. Wpisz 'quit' aby wyjść.\n")
    history = []
    while True:
        user_input = input("Ty: ").strip()
        if user_input.lower() in ("quit", "exit", "q"):
            break
        if not user_input:
            continue
      
        answer, history, f_count, srcs = chat(history, user_input)
        print(f"Asystent: {answer}\n[Źródła: {', '.join(srcs)} | Fragmenty: {f_count}]\n")
