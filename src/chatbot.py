"""
Osoba 2 — logika chatbota: integracja OpenAI, retrieval, historia rozmowy.
"""

import os
from openai import OpenAI
from dotenv import load_dotenv
from retrieval import search

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


def build_prompt(user_question: str) -> str:
    chunks = search(user_question, n_results=3)
    context = "\n\n---\n\n".join(chunks)
    return f"Kontekst z bazy wiedzy:\n{context}\n\nPytanie: {user_question}"


def chat(history: list[dict], user_message: str) -> tuple[str, list[dict]]:
    """Wysyła wiadomość i zwraca odpowiedź + zaktualizowaną historię."""
    augmented = build_prompt(user_message)
    history.append({"role": "user", "content": augmented})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history,
        max_tokens=512,
        temperature=0.3,
    )

    reply = response.choices[0].message.content
    history.append({"role": "assistant", "content": reply})
    return reply, history


if __name__ == "__main__":
    print("RPG Asystent gotowy. Wpisz 'quit' aby wyjść.\n")
    history = []
    while True:
        user_input = input("Ty: ").strip()
        if user_input.lower() in ("quit", "exit", "q"):
            break
        if not user_input:
            continue
        answer, history = chat(history, user_input)
        print(f"Asystent: {answer}\n")
