"""
Osoba 2 — prosty interfejs Gradio.
"""

import gradio as gr
from chatbot import chat

history_state = []


def respond(user_message: str, chat_history: list) -> tuple[str, list]:
    global history_state
    reply, history_state = chat(history_state, user_message)
    chat_history.append({"role": "user", "content": user_message})
    chat_history.append({"role": "assistant", "content": reply})
    return "", chat_history


with gr.Blocks(title="RPG Asystent") as demo:
    gr.Markdown("# RPG Asystent\nZadaj pytanie o zasady gry, klasy postaci, zaklęcia i więcej.")
    chatbot = gr.Chatbot(height=400)
    msg = gr.Textbox(placeholder="Zapytaj o zasady RPG...", label="Twoje pytanie")
    clear = gr.Button("Wyczyść")

    msg.submit(respond, [msg, chatbot], [msg, chatbot])
    clear.click(lambda: ([], []), outputs=[chatbot])

if __name__ == "__main__":
    demo.launch()
