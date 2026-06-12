"""
Osoba 2 — interfejs Gradio
"""

import gradio as gr
from chatbot import chat

# ──────────────────────────────────────────────────────────────────────────
# State & callbacks
# ──────────────────────────────────────────────────────────────────────────

history_state: list = []

def respond(user_message: str, chat_history: list):
    """Przetwarza wiadomość i zwraca zaktualizowaną historię oraz statystyki."""
    global history_state

    if not user_message.strip():
        # Zwracamy bez zmian, jeśli puste
        return "", chat_history, gr.update(), gr.update()

    reply, history_state, frag_count, sources = chat(history_state, user_message)
    
    # Obliczamy liczbę wiadomości w sesji (połowa długości historii)
    msg_count = len(history_state) // 2
    
    session_html = f"<b>Wiadomości w sesji:</b> {msg_count}"
    
    source_str = ", ".join(sources) if sources else "Brak"
    retrieval_html = f"<b>Pobrane fragmenty:</b> {frag_count}<br><b>Źródła:</b> {source_str}"

    return "", history_state, session_html, retrieval_html

def clear_history():
    """Resetuje historię rozmowy oraz statystyki."""
    global history_state
    history_state = []
    
    default_session = "<b>Wiadomości w sesji:</b> 0"
    default_retrieval = "<b>Pobrane fragmenty:</b> 0<br><b>Źródła:</b> Brak"
    
    return [], default_session, default_retrieval

def quick_ask(prompt: str, chat_history: list):
    """Wysyła szybkie zapytanie przez standardowy flow."""
    return respond(prompt, chat_history)


# ──────────────────────────────────────────────────────────────────────────
# Static content
# ──────────────────────────────────────────────────────────────────────────

QUICK_PROMPTS = [
    ("⚔️ Klasy postaci", "Jakie są klasy postaci w D&D 5e?"),
    ("🧙 Zaklęcia", "Jakie są najpotężniejsze zaklęcia w D&D?"),
    ("🎲 Walka", "Wyjaśnij zasady walki w D&D 5e"),
    ("🗡️ Broń", "Jaką broń wybrać dla wojownika?"),
    ("🧝 Rasy", "Jakie rasy mogę wybrać w D&D 5e?"),
]

HEADER_HTML = """
<div id="rpg-header">
    <h1 id="rpg-title">RPG Asystent</h1>
    <p id="rpg-subtitle">Dungeons &amp; Dragons 5e</p>
</div>
"""

FOOTER_HTML = """
<div id="rpg-footer">
    ⚔ &nbsp; RAG · ChromaDB · GPT-4o-mini &nbsp;·&nbsp; Systemy Dialogowe 2026 &nbsp; ⚔
</div>
"""

PLACEHOLDER_HTML = """
<div style="text-align:center;padding:3rem 1rem;color:#2A2838">
    <div style="font-size:2.5rem;margin-bottom:0.75rem">⚔️</div>
    <div style="font-family:Cinzel,serif;font-size:0.9rem;letter-spacing:0.12em">
        Zadaj pierwsze pytanie, Wędrowcze
    </div>
</div>
"""


# ──────────────────────────────────────────────────────────────────────────
# CSS
# ──────────────────────────────────────────────────────────────────────────

def _load_css() -> str:
    return """
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Inter:wght@300;400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body {
    min-height: 100%;
    margin: 0;
    overflow-y: auto;
}

body, .gradio-container {
    background: #FDFDFD !important;
    font-family: 'Inter', sans-serif !important;
    color: #1F2937 !important;
}

.gradio-container {
    max-width: 1400px !important; /* Poszerzono dla 2 kolumn */
    width: 100% !important;
    min-height: 100vh !important;
    margin: 0 auto !important;
    padding: 0.6rem 0.6rem 0.6rem !important;
    display: flex !important;
    flex-direction: column !important;
    gap: 0.85rem !important;
}

footer { display: none !important; }

/* ── Header ── */
#rpg-header {
    text-align: center;
    margin-bottom: 0.8rem;
    padding: 0.5rem 0.5rem 0;
}

#rpg-header::after {
    content: '';
    display: block;
    height: 1px;
    background: linear-gradient(90deg,
        transparent 0%, #A3AED0 30%,
        #64748B 50%, #A3AED0 70%, transparent 100%);
    margin-top: 0.85rem;
}

#rpg-title {
    font-family: 'Cinzel', serif !important;
    font-size: clamp(1.5rem, 2.8vw, 2rem) !important;
    font-weight: 700 !important;
    letter-spacing: 0.04em;
    color: #111827 !important;
    margin-bottom: 0.15rem;
    line-height: 1.05;
}

#rpg-subtitle {
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    color: #475569 !important;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}

/* ── Chatbot ── */
#rpg-chatbot {
    background: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 18px !important;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08) !important;
    min-height: 420px !important;
    height: clamp(420px, 55vh, 760px) !important;
    width: 100% !important;
    overflow: hidden !important;
}

#rpg-chatbot > div { background: transparent !important; }
#rpg-chatbot .chatbot > div { overflow-y: auto !important; padding-right: 0.3rem !important; }

#rpg-chatbot .user,
#rpg-chatbot .bot,
#rpg-chatbot .user .bubble-wrap,
#rpg-chatbot .bot .bubble-wrap {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
}

#rpg-chatbot .user .bubble-wrap,
#rpg-chatbot .bot .bubble-wrap { display: contents !important; }

#rpg-chatbot .user div.message,
#rpg-chatbot .bot div.message {
    max-width: 150% !important;
    width: auto !important;
    padding: 1rem 1.4rem !important;
    line-height: 1.65 !important;
    margin: 0 !important;
    word-break: break-word !important;
    white-space: normal !important;
}

#rpg-chatbot .user div.message {
    background: #F3E8FF !important;
    border: 1px solid #D8B4FE !important;
    border-radius: 18px 18px 4px 18px !important;
    color: #1F2937 !important;
    box-shadow: 0 2px 10px rgba(167, 139, 250, 0.12) !important;
}

#rpg-chatbot .bot div.message {
    background: #F8FAFC !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 18px 18px 18px 4px !important;
    color: #0F172A !important;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.06) !important;
}

#rpg-chatbot .user .avatar-container { display: none !important; }

#rpg-chatbot .bot .avatar-container {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 38px !important;
    height: 38px !important;
    min-width: 38px !important;
    margin-right: 0.9rem !important;
    border-radius: 50% !important;
    background: #E9D5FF !important;
    border: 1px solid #D8B4FE !important;
    box-shadow: 0 4px 12px rgba(167, 139, 250, 0.18) !important;
}

#rpg-chatbot .bot .avatar-container::before {
    content: "🛡️" !important;
    font-size: 1rem !important;
}

/* ── Textbox ── */
#rpg-input textarea {
    background: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 14px !important;
    color: #0F172A !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 1rem !important;
    padding: 1rem 1.1rem !important;
    transition: border-color 0.2s, box-shadow 0.25s !important;
}

#rpg-input textarea:focus {
    border-color: #2563EB !important;
    box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.12) !important;
    outline: none !important;
}

#rpg-input textarea::placeholder { color: #94A3B8 !important; }
#rpg-input label > span:first-child { display: none !important; }

/* ── Buttons ── */
#send-btn, #clear-btn {
    border-radius: 14px !important;
    font-family: 'Cinzel', serif !important;
    font-size: 0.86rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.04em !important;
    transition: transform 0.18s ease, box-shadow 0.18s ease !important;
    border: none !important;
    min-width: 100px !important;
    height: 48px !important;
}

#send-btn {
    background: linear-gradient(135deg, #C4B5FD, #A78BFA) !important;
    color: #111827 !important;
    box-shadow: 0 10px 24px rgba(167, 139, 250, 0.24) !important;
}

#send-btn:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 24px rgba(37, 99, 235, 0.22) !important;
}

#clear-btn {
    background: #FFFFFF !important;
    color: #334155 !important;
    border: 1px solid #CBD5E1 !important;
    box-shadow: 0 6px 16px rgba(148, 163, 184, 0.16) !important;
}

#clear-btn:hover {
    background: #F1F5F9 !important;
    color: #0F172A !important;
    transform: translateY(-1px) !important;
}

/* ── Side Panel ── */
.side-panel-title {
    font-family: 'Cinzel', serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: #111827;
    margin-bottom: 0.6rem;
    border-bottom: 1px solid #CBD5E1;
    padding-bottom: 0.3rem;
}

.stat-box {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 0.75rem;
    font-size: 0.85rem;
    color: #334155;
    margin-bottom: 0.5rem;
    line-height: 1.5;
}

.about-blurb {
    background: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 0.85rem;
    font-size: 0.85rem;
    color: #475569;
    line-height: 1.6;
    box-shadow: 0 4px 6px rgba(15, 23, 42, 0.05);
}

/* ── Quick prompts ── */
.quick-title {
    font-size: 0.95rem;
    font-weight: 700;
    color: #334155;
    margin-bottom: 0.4rem;
    letter-spacing: 0.02em;
}

.gradio-row .qbtn { flex-wrap: wrap !important; gap: 0.4rem !important; }

.qbtn button {
    background: #F8FAFC !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 999px !important;
    color: #334155 !important;
    font-size: 0.92rem !important;
    font-family: 'Inter', sans-serif !important;
    padding: 0.6rem 1.1rem !important;
    min-width: 120px !important;
    min-height: 42px !important;
    transition: all 0.15s !important;
}

.qbtn button:hover {
    border-color: #93C5FD !important;
    color: #1D4ED8 !important;
    background: #EFF6FF !important;
}

/* ── Footer ── */
#rpg-footer {
    text-align: center;
    margin-top: 1.5rem;
    font-size: 0.75rem;
    color: #64748B;
    letter-spacing: 0.08em;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: #F8FAFC; }
::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 999px; }
::-webkit-scrollbar-thumb:hover { background: #94A3B8; }

@media (max-width: 900px) {
    .gradio-container { padding: 0.5rem 0.5rem 0.75rem !important; }
    #rpg-title { font-size: 1.5rem !important; }
    #rpg-chatbot { min-height: 360px !important; max-height: 360px !important; }
    #send-btn, #clear-btn { height: 44px !important; min-width: 90px !important; }
}
"""


# ──────────────────────────────────────────────────────────────────────────
# UI sections
# ──────────────────────────────────────────────────────────────────────────

def _build_chat_panel() -> tuple[gr.Chatbot, gr.Textbox, gr.Button, gr.Button]:
    chatbot = gr.Chatbot(
        elem_id="rpg-chatbot",
        height=520,
        show_label=False,
        placeholder=PLACEHOLDER_HTML,
    )

    with gr.Row():
        msg = gr.Textbox(
            placeholder="Zapytaj o zasady, klasy, zaklęcia, potwory…",
            show_label=False,
            elem_id="rpg-input",
            scale=8,
            lines=1,
            max_lines=5,
            autofocus=True,
            submit_btn=False,
        )
        send_btn = gr.Button("Wyślij ⚡", elem_id="send-btn", scale=2, variant="primary")
        clear_btn = gr.Button("✕ Wyczyść", elem_id="clear-btn", scale=2)

    return chatbot, msg, send_btn, clear_btn


def _build_quick_prompts(chatbot: gr.Chatbot, msg: gr.Textbox, session_stats: gr.HTML, retrieval_stats: gr.HTML) -> None:
    gr.HTML('<div class="quick-title">Szybkie pytania</div>')

    with gr.Row():
        for label, prompt in QUICK_PROMPTS:
            button = gr.Button(label, elem_classes=["qbtn"], size="md", scale=2)
            button.click(
                fn=quick_ask,
                inputs=[gr.State(value=prompt), chatbot],
                outputs=[msg, chatbot, session_stats, retrieval_stats],
            )


def _build_side_panel() -> tuple[gr.HTML, gr.HTML]:
    """Tworzy prawy panel ze statystykami i informacją o projekcie."""
    gr.HTML('<div class="side-panel-title">Wydajność i Źródła</div>')
    
    retrieval_stats = gr.HTML(
        value="<div class=\"about-blurb\"><b>Pobrane fragmenty:</b> 0<br><b>Źródła:</b> Brak</div>"
    )
    
    session_stats = gr.HTML(
        value="<div class=\"about-blurb\"><b>Wiadomości w sesji:</b> 0</div>"
    )
        
    gr.HTML('<div class="side-panel-title" style="margin-top: 1.5rem;">O projekcie</div>')
    gr.HTML("""
    <div class="about-blurb">
        <strong>RPG Asystent</strong> wspiera graczy D&D 5e w wyszukiwaniu zasad, czarów i mechanik z podręczników.
        To Twój podręczny, cyfrowy pomocnik, który czuwa nad płynnością rozgrywki i w mgnieniu oka rozwiewa wszelkie wątpliwości dotyczące reguł gry.
    </div>
    """)
    
    return retrieval_stats, session_stats


def _wire_events(chatbot, msg, send_btn, clear_btn, session_stats, retrieval_stats) -> None:
 
    outputs = [msg, chatbot, session_stats, retrieval_stats]
    
    msg.submit(respond, [msg, chatbot], outputs)
    send_btn.click(respond, [msg, chatbot], outputs)
    
    clear_btn.click(
        fn=clear_history, 
        inputs=[], 
        outputs=[chatbot, session_stats, retrieval_stats]
    )


# ──────────────────────────────────────────────────────────────────────────
# App 
# ──────────────────────────────────────────────────────────────────────────

def build_ui() -> gr.Blocks:
    with gr.Blocks(title="⚔️ RPG Asystent", css=_load_css()) as demo:
        gr.HTML(HEADER_HTML)

    
        with gr.Row():
            with gr.Column(scale=3):
                chatbot, msg, send_btn, clear_btn = _build_chat_panel()
                
            with gr.Column(scale=1):
                retrieval_stats, session_stats = _build_side_panel()
        _build_quick_prompts(chatbot, msg, session_stats, retrieval_stats)
        
        gr.HTML(FOOTER_HTML)

        _wire_events(chatbot, msg, send_btn, clear_btn, session_stats, retrieval_stats)

    return demo


if __name__ == "__main__":
    build_ui().launch()
