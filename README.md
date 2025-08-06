# Offline AI Language Learning Assistant

An **offline**, **privacy-first** AI-powered language learning tool that helps you **translate**, **define**, and **practice vocabulary** directly from any text — **no internet required**.

Powered by the **Gemma 3n** language model running locally via **Ollama**, this tool provides context-aware translations, definitions, example sentences, and related word suggestions. All results are stored locally in your personal dictionary for review anytime.

---

## ✨ Features

- **Offline AI Processing** — Works entirely offline for maximum privacy.
- **Context-Aware Translations** — Extracts key content words, lemmatizes them, and translates them into your target language.
- **Smart Definitions** — Generates short, precise definitions based on the word's meaning in your specific context.
- **Example Sentences** — Creates simple, clear example sentences to reinforce learning.
- **Semantic Similar Words** — Finds related vocabulary using Retrieval-Augmented Generation (RAG) with FAISS + MiniLM embeddings.
- **Personal Dictionary** — Saves all words, translations, definitions, and examples to a local JSON file for future review.
- **Multilingual Support** — Works with multiple languages (English, Russian, Korean, Chinese, Japanese, Spanish, French, German, Italian, Portuguese).


---

## 🛠️ How It Works

1. **Input any text** — e.g., a news article, a short story, or a paragraph you want to learn from.
2. **Word extraction & lemmatization** — Only the most important content words are kept, in their base dictionary form.
3. **Translation** — Words are translated into your target language.
4. **Definition generation** — The model generates short, clear definitions that fit the context of your text.
5. **Example creation** — Simple, natural example sentences are generated for each word.
6. **Related words search** — The app finds semantically similar words from your personal dictionary.
7. **Local storage** — Everything is saved offline in `dictionary.json`.

---

## 🧠 Tech Stack

- **[Ollama](https://ollama.ai/)** — Runs Gemma 3n locally for translations, definitions, and examples.
- **Gemma 3n** — Multilingual, on-device LLM for fast and private language processing.
- **LangGraph** — Modular, node-based pipeline execution.
- **FAISS** — High-performance vector search for semantic similarity.
- **MiniLM Embeddings** — Lightweight, accurate sentence embeddings for similarity search.
- **Python** — Core programming language for app logic.

---
```python
test_state = {
        'text':text_en, 
        'src_language':'en',
        'tgt_language':'ko',
        'words':set(text_en.split()),
        "translations": {'park': []},
        "definitions": {'park': []},
        "examples": {'park': []},
        "examples_number": {'park': 1},
        "similar_words": {'park': []},
        "saved_to_json":False
}

compiled_graph.invoke(test_state)
```
## [Output](dictionary.json)

## 🔮Future Plans
Spaced repetition system for optimized review.

Interactive quizzes for active recall practice.

Multimodal support — learn from audio and images.

Custom export formats for Anki or flashcards.

## 🙌Acknowledgments
Ollama for running Gemma 3n locally.

LangGraph for the pipeline architecture.

FAISS for semantic similarity search.

HuggingFace for MiniLM embeddings.
