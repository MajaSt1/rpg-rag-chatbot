"""
Osoba 2 — logika chatbota: integracja OpenAI, retrieval, historia rozmowy.
"""

import os
from openai import OpenAI
from dotenv import load_dotenv
from retrieval import search

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """Jesteś asystentem RPG — ekspertem od gier fabularnych.
Odpowiadaj WYŁĄCZNIE na podstawie dostarczonego kontekstu z bazy wiedzy.
Jeśli odpowiedź nie wynika z kontekstu, powiedz: "Nie mam tej informacji w bazie wiedzy."
Odpowiadaj po polsku, zwięźle i konkretnie."""


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
