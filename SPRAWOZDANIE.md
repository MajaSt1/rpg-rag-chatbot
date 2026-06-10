# Sprawozdanie — RPG RAG Chatbot

**Przedmiot:** Systemy Dialogowe
**Projekt:** Asystent do gier fabularnych (RPG) oparty na RAG

---

## 1. Cel projektu

Zbudowanie chatbota, który odpowiada na pytania o gry fabularne (Dungeons & Dragons 5e)
wyłącznie na podstawie własnej bazy wiedzy, z wykorzystaniem techniki
**RAG (Retrieval-Augmented Generation)**. Dzięki temu odpowiedzi są oparte na
dostarczonych dokumentach, a nie na ogólnej wiedzy modelu — co ogranicza halucynacje.

## 2. Architektura

```
Pytanie użytkownika
    ↓
[Routing]       — klasyfikacja typu pytania (zwykłe vs agregujące)
    ↓
[R] Retrieval   — pobranie kontekstu z bazy: fragmenty (próg podobieństwa)
                  albo cały dokument (tryb agregacji)
    ↓
[A] Augmentation — wklejenie kontekstu do promptu jako "Kontekst z bazy wiedzy"
    ↓
[G] Generation  — gpt-4o-mini generuje odpowiedź na podstawie kontekstu
```

| Etap | Plik | Opis |
|------|------|------|
| Routing | `src/chatbot.py` → `classify_query` | rozpoznanie pytania agregującego, wybór ścieżki |
| Retrieval | `src/retrieval.py` | embeddingi `text-embedding-3-small`, `search` (próg podobieństwa) lub `get_full_document` (cały plik) |
| Augmentation | `src/chatbot.py` → `build_prompt` | sklejenie kontekstu + pytania |
| Generation | `src/chatbot.py` → `chat` | wywołanie `gpt-4o-mini`, `temperature=0.3` |
| Interfejs | `src/ui.py` | prosty UI w Gradio |

## 3. Baza wiedzy

Baza składa się z **14 plików tematycznych** (`data/*.txt`) podzielonych na
**142 fragmenty** (chunki). Chunking jest **semantyczny** (`parse_text_semantically`):
dokumenty dzielone są po nagłówkach sekcji (`=== NAGŁÓWEK ===`), a każdy fragment dostaje
metadane (`source`, `section`). Dzięki temu jeden chunk = jedna spójna sekcja (np. opis
jednej klasy), zamiast cięcia na sztywno co N znaków.

Zakres tematyczny: klasy postaci, rasy, zaklęcia, ekwipunek, zasady walki, bestiariusz,
artefakty, świat i lore, przygody/kampanie, pułapki i zagadki, porady dla MG, interakcje z NPC,
tła postaci, umiejętności i mechaniki.

## 4. Wektory znaczeniowe (embeddingi)

Każdy fragment jest zamieniany na wektor liczb (embedding) modelem `text-embedding-3-small`.
Wyszukiwanie polega na zamianie pytania na wektor i znalezieniu fragmentów o najbliższych
wektorach (podobieństwo kosinusowe). Dzięki temu pytanie „jak czarodziej odzyskuje zaklęcia?"
pasuje do fragmentu o „Arcane Recovery", mimo braku identycznych słów.

## 5. Napotkane problemy i ich rozwiązania

| Problem | Przyczyna | Rozwiązanie |
|---------|-----------|-------------|
| `RateLimitError 429 insufficient_quota` | brak środków na koncie OpenAI API (ChatGPT Plus ≠ API) | wykupienie planu Prototype ($5) |
| `Data incompatible with messages format` (Gradio) | Gradio 6 wymaga formatu `messages` (słowniki `role`/`content`), kod używał krotek | przepisanie `respond()` na format słownikowy |
| Pytania porównawcze zwracały „Nie mam tej informacji" | retrieval pobierał stałą, zbyt małą liczbę fragmentów (`n_results=3`) | zastąpienie stałej liczby **progiem podobieństwa** (patrz sekcja 6) |

## 6. Strategia wyszukiwania i ograniczenia RAG — kluczowa obserwacja

### 6.1. Od stałej liczby fragmentów do progu podobieństwa

Pierwsza wersja pobierała **stałą** liczbę fragmentów (`n_results`). Okazało się to złym
kompromisem, bo różne typy pytań potrzebują różnej ilości kontekstu:

| Typ pytania | Potrzebny kontekst | Efekt stałej liczby |
|-------------|--------------------|---------------------|
| Proste („Ile HP ma Wojownik?") | 2–3 fragmenty | przy dużym `n` nadmiar fragmentów = szum |
| Porównawcze („Ile HP ma Wojownik, a ile Barbarzyńca?") | kilka fragmentów | OK |
| Agregujące („Która klasa ma **najwięcej** HP?") | wszystkie klasy | niepełne dane → błędna odpowiedź |

Dlatego zastąpiliśmy stałą liczbę **progiem podobieństwa** (`SIMILARITY_THRESHOLD` w
`retrieval.py`). Zamiast „zawsze N fragmentów", funkcja `search` pobiera pulę kandydatów
(`CANDIDATE_POOL = 15`), liczy podobieństwo (`1 − odległość kosinusowa`) i zwraca **tylko te
powyżej progu**. Liczba zwróconych fragmentów dopasowuje się więc do pytania. Bezpiecznik
(`MIN_RESULTS = 2`) gwarantuje, że nigdy nie zwracamy pustego kontekstu.

### 6.2. Dobór progu — analiza empiryczna

Próg dobraliśmy na podstawie pomiarów podobieństwa dla różnych pytań:

| Próg | „Ile HP ma Wojownik?" | „Cecha Paladyna?" | pytanie szerokie | pytanie obce (spaghetti) |
|------|----------------------|-------------------|------------------|--------------------------|
| 0.45 | 15 fragm. (za dużo) | 7 | 5 | 2 |
| **0.47 (wybrane)** | **7** | **3** | **3** | **2** |
| 0.50 | 2 | 2 | 2 | 2 (za agresywne) |

Wybraliśmy **0.47**: pytania konkretne dostają mniej fragmentów, a pytanie kompletnie
spoza dziedziny („przepis na spaghetti") spada do minimum (sam bezpiecznik).

### 6.3. Ważne ograniczenie progu: dane są semantycznie zbite

Istotna obserwacja: **cała baza dotyczy D&D**, więc embeddingi wszystkich fragmentów są do
siebie podobne. W praktyce podobieństwa trafnych i mniej trafnych fragmentów RPG kłębią się
blisko siebie (ok. 0.44–0.48), a wyraźnie odstaje dopiero treść spoza dziedziny (~0.38).
Próg dobrze **odsiewa treści obce**, ale słabo rozróżnia „najlepszy fragment RPG" od „przeciętnego
fragmentu RPG". Prawdziwym sygnałem trafności jest **spadek (cliff)** podobieństwa po 1–2
najlepszych wynikach, a nie wartość bezwzględna — co trudno ująć prostym progiem.

### 6.4. Pytania agregujące i ich rozwiązanie — routing zapytań

Pytania typu „która z **wszystkich** klas ma najwięcej HP?" są dla zwykłego RAG trudne —
wymagają **kompletu** danych, a wyszukiwanie po podobieństwie z natury zwraca tylko *podzbiór*
fragmentów. Pierwotnie model na pytanie „Jaka klasa jest najtwardsza (najwięcej HP)?" udzielał
**pewnej, ale błędnej** odpowiedzi (wskazywał Wojownika 1d10, podczas gdy Barbarzyńca ma 1d12) —
ponieważ fragment o Barbarzyńcy w ogóle nie trafiał do pobranego kontekstu.

**Rozwiązanie: routing zapytań** (`classify_query` w `chatbot.py`). Przed pobraniem kontekstu
tani model (`gpt-4o-mini`) klasyfikuje, czy pytanie jest *agregujące*, i jeśli tak — wskazuje,
który dokument bazy wczytać w **całości**:

```
Pytanie → classify_query()
   ├─ AGREGUJĄCE → get_full_document(pliki)  → całe dokumenty (komplet danych)
   └─ ZWYKŁE     → search()                  → fragmenty pasujące do pytania
```

Po wdrożeniu pytanie „która z wszystkich klas ma najwięcej HP?" zwraca poprawnie
**„Barbarzyńca, 1d12"**. Routing jest **skalowalny** — klasyfikator dostaje listę wszystkich
plików bazy, więc np. „ile jest ras?" sam kieruje do `rasy.txt`, bez żadnej listy słów kluczowych.

**Zgodność z wymaganiem projektu:** model językowy służy tu wyłącznie do *klasyfikacji typu
pytania* (wybór ścieżki). Właściwa odpowiedź jest **zawsze** generowana na podstawie kontekstu
z bazy wiedzy — w obu ścieżkach dane pochodzą z plików `data/`, nigdy z samej wiedzy modelu.

### 6.5. Routing wielodokumentowy

Niektóre pytania **łączą tematy** i wymagają kilku dokumentów naraz, np. „która klasa najlepiej
współgra z rasą krasnoluda?" potrzebuje *i* `klasy_postaci.txt`, *i* `rasy.txt`. Dlatego
`classify_query` zwraca **listę** plików (nie jeden), a `build_prompt` skleja wszystkie wskazane
dokumenty w jeden kontekst. Dla pytania o krasnoluda klasyfikator poprawnie wskazuje oba pliki.

### 6.6. Siatka bezpieczeństwa klasyfikatora

Klasyfikator oparty na LLM bywa **niedeterministyczny na pytaniach granicznych** — np. „która
klasa ma najmniej HP?" bywało przeoczane, mimo że „najwięcej HP" było rozpoznawane. Aby to
ustabilizować, dodaliśmy **siatkę bezpieczeństwa**: lista słów-sygnałów typowych dla agregacji
(`AGGREGATION_SIGNALS`: „najwięcej", „najmniej", „wszystkie", „ile jest"…). Jeśli klasyfikator
zwróci pustą listę, ale pytanie zawiera taki sygnał, **ponawiamy klasyfikację z wymuszeniem
wyboru pliku** (zakaz odpowiedzi „NONE").

Ważne: słowa-sygnały służą tylko do **wykrycia, że pytanie jest agregujące** — *który* plik
wczytać decyduje nadal klasyfikator LLM. To istotna różnica wobec odrzuconego wcześniej podejścia
„czystych słów kluczowych" (które na sztywno mapowało słowo → plik). Dzięki temu rozwiązanie
pozostaje skalowalne, a zarazem odporne na wahania klasyfikatora. Po dodaniu siatki „najmniej HP"
poprawnie zwraca **Czarodziej 1d6**.

### 6.7. Koszt rozwiązania

Routing dodaje jedno krótkie wywołanie klasyfikujące na pytanie (`max_tokens=60`), groszowy
koszt; w rzadkich przypadkach siatki bezpieczeństwa — drugie. W zamian tryb agregacji wczytuje
całe dokumenty (np. `klasy_postaci.txt` ~5300 tokenów) — porównywalnie do kilkunastu fragmentów,
a z gwarancją kompletu danych.

## 7. Możliwe dalsze ulepszenia (poza zakresem projektu)

- **Re-ranking** — pobranie większej puli kandydatów i przesortowanie ich osobnym modelem
  rankującym; lepiej radzi sobie ze zbitymi podobieństwami (sekcja 6.3) niż sam próg.
- **Próg adaptacyjny** — wykrywanie „cliffa" podobieństwa zamiast stałej wartości progu.
- **Klasyfikator fine-tunowany** — zastąpienie klasyfikacji promptem małym, dotrenowanym
  modelem, by usunąć niedeterminizm na pytaniach granicznych (sekcja 6.6) bez siatki słów-sygnałów.

## 8. Wnioski

RAG skutecznie odpowiada na pytania faktograficzne i porównania, ograniczając halucynacje
dzięki zasadzie „odpowiadaj tylko z kontekstu". W trakcie projektu zastosowaliśmy usprawnienia
ponad podstawowy RAG: (1) zastąpienie stałej liczby fragmentów **progiem podobieństwa**, dzięki
czemu liczba pobieranych fragmentów dopasowuje się do pytania; (2) **routing zapytań** z
klasyfikatorem intencji, który rozwiązuje pytania agregujące przez wczytanie całych dokumentów —
także **wielu naraz** dla pytań łączących tematy; oraz (3) **siatkę bezpieczeństwa** stabilizującą
klasyfikator na pytaniach granicznych. W każdej ścieżce odpowiedź pochodzi z własnej bazy wiedzy.
Pozostałe ograniczenia (zbite podobieństwa w wąsko-tematycznej bazie, niedeterminizm klasyfikatora
promptowego) wynikają z natury wyszukiwania po podobieństwie i klasyfikacji LLM, i wskazują
kierunki dalszej pracy (re-ranking, próg adaptacyjny, klasyfikator dotrenowany).
