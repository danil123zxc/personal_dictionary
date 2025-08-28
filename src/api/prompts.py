"""
AI Prompts Module

This module contains the prompt templates used by the AI language models
for generating translations, definitions, and examples. These prompts are
designed to work with structured output models to ensure consistent and
reliable results.

Features:
- Translation prompts for extracting and translating content words
- Definition prompts for generating word definitions
- Example prompts for creating usage examples
- Structured output formatting for consistent results

Usage:
    These prompts are used by the generate.py module with LangChain's
    structured output capabilities to ensure the AI models return
    data in the expected format.

Prompt Design Principles:
- Clear, specific instructions to avoid ambiguity
- Structured output requirements for consistent parsing
- Context-aware processing for better accuracy
- Language-specific guidance for proper translations
"""

# Translation prompt for extracting and translating content words from text
translation_prompt = """
    You receive a text.

    Task:
    1. For each sentence, extract all **content words** only (exclude stopwords such as articles, prepositions, conjunctions, auxiliaries, pronouns, names).
    2. Convert each extracted word to its **base dictionary form (lemma)** — for example: "told" → "tell", "running" → "run".
    3. Translate each lemma from {src_language} to **{tgt_language}** (use the target language exactly as provided, not English by default).
    4. Remove duplicates — only include unique lemmas for the whole input text.

    Only include unique words per input (no duplicates).
    Do not add extra explanations or context.
    """

# Definition prompt for generating word definitions in specific languages
definition_prompt = """
    Generate a single definition for the word in {language}, based only on its meaning in the given sentence:

    Rules:
    1. Provide exactly one short, clear definition matching the word's meaning in this sentence.
    2. No other meanings, no examples.
    3. The definition must be in {language}.
    4. If unsure give your best guess.

"""

# Example prompt for generating usage examples for words
example_prompt = """
    Generate {examples_number} simple sentences for the word in {language} using only the given definition:
    Rules:
    1. Sentences must match this definition exactly; ignore other meanings.
    2. Grammar must be correct and natural.
    3. Use simple, clear vocabulary for learners.
    4. Avoid repeating the same structure or idea.
    5. If definition is not given use the most common meaning of this word.
    """
