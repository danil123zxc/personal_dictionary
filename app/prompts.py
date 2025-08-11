translation_prompt = """
You receive a text.

Task:
1. For each sentence, extract all **content words** only (exclude stopwords such as articles, prepositions, conjunctions, auxiliaries, pronouns, names).
2. Convert each extracted word to its **base dictionary form (lemma)** — for example: "told" → "tell", "running" → "run".
3. Translate each lemma from {src_language} to **{tgt_language}** (use the target language exactly as provided, not English by default).
4. Remove duplicates — only include unique lemmas for the whole input text.
5. Output as a JSON object in the format:
    {{
        'word1': ['translation'],
        'word2': ['translation']
    }}
Only include unique words per input (no duplicates).
Do not add extra explanations or context.

Input text:
"{text}"

    """

definition_prompt = """
    Generate a single definition for the word "{word}" in {language}, based only on its meaning in the given sentence:

    Sentence:
    "{context}"

    Rules:
    1. Provide exactly one short, clear definition matching the word's meaning in this sentence.
    2. No other meanings, no examples.
    3. The definition must be in {language}.
    4. If unsure, mark as such and give your best guess.

    Return JSON only in the format:
    {{
        "definition": ["single definition"], 
    }}
"""

example_prompt = """
    Generate {examples_number} simple sentences for "{word}" in {language} using only the given definition:

    Definition:
    "{definition}"

    Rules:
    1. Sentences must match this definition exactly; ignore other meanings.
    2. Grammar must be correct and natural.
    3. Use simple, clear vocabulary for learners.
    4. Avoid repeating the same structure or idea.
    5. "message" field is only for missing/uncertain examples or rare meanings.

    Output JSON only:

    {{
        "examples": ["example sentence 1", ...],
    }}

    """
