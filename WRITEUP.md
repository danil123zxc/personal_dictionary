# Technical Writeup: Offline AI Language Learning Application Using Gemma 3n and LangGraph

## 1. Introduction

This project is an offline AI-powered language learning assistant designed to help users build vocabulary effectively by extracting, translating, defining, and exemplifying words from various input sources such as text, audio, and images.

The application focuses on operating entirely offline to preserve user privacy and data security, generating context-sensitive translations and definitions, providing learner-friendly example sentences, suggesting semantically related words to enrich vocabulary, and maintaining a persistent vocabulary dictionary for review and spaced repetition.

The system leverages the Gemma 3n language model running locally via Ollama, orchestrated through a LangGraph pipeline, enhanced with Retrieval-Augmented Generation (RAG) using FAISS and MiniLM embeddings.

## 2. System Architecture Overview

The core of the system is a pipeline of NLP processing nodes, managed by LangGraph's `StateGraph`. Each node encapsulates a single transformation or generation step, passing along a shared `state` dictionary containing all relevant intermediate data.

Key pipeline stages include:

- **translate_words:** Extract content words and generate translations.
- **generate_definitions:** Produce clear, context-aware definitions for each word.
- **generate_examples:** Generate simple, natural example sentences per word.
- **generate_similar:** Retrieve semantically related words using RAG (FAISS).
- **save_to_json:** Merge all data and save the full dictionary to a JSON file.

This structured pipeline ensures modularity, maintainability, and extensibility, facilitating debugging and future improvements.
<img width="186" height="623" alt="image" src="https://github.com/user-attachments/assets/80a6ab62-4715-4f6e-9250-374ba1fbc981" />

## 3. Detailed Node Descriptions

### 3.1 translate_words_node

Input: Raw text, source and target languages.

Process: Uses a custom translation prompt to extract only content words (excluding stopwords), lemmatize each word, and translate lemmas into the target language. Parses the JSON response into a dictionary mapping words to lists of translations.

Output: Set of unique words for further processing and dictionary of translations.

### 3.2 generate_definitions_node

Input: Words from previous step, source language.

Process: For each word, generate a single short definition using context (original sentence). This uses a dedicated definition prompt instructing Gemma 3n to provide concise, sense-specific definitions.

Output: Updated dictionary mapping words to their definitions.

### 3.3 generate_examples_node

Input: Words with definitions and requested number of examples.

Process: For each word, generate simple example sentences strictly matching the definition. This ensures grammatical correctness and vocabulary appropriateness for learners.

Output: Dictionary mapping words to example sentence lists.

### 3.4 generate_similar_node

Input: Words and text context.

Process: Uses a Retrieval-Augmented Generation (RAG) retriever backed by FAISS and MiniLM embeddings to find semantically similar words already in the user’s dictionary. This helps discover synonyms, related concepts, and avoids redundant LLM calls.

Output: Dictionary mapping words to lists of similar words.

### 3.5 save_to_json_node

Input: Aggregated data of words, translations, definitions, and examples.

Process: Merges data into a comprehensive dictionary keyed by (source language, target language) tuples and saves it to disk as JSON with Unicode preservation and indentation for readability. Catches and logs any file or serialization errors gracefully.

Output: Confirmation boolean of success and the merged dictionary.

## 4. Gemma 3n Usage

Gemma 3n is a multilingual, quantized LLM optimized for local deployment with Ollama. It balances model size and performance, enabling fast inference without cloud dependency. It supports complex language tasks such as translation, definition generation, and text generation.

The integration uses carefully engineered prompts and parses responses as strict JSON to maintain structured outputs. Prompt engineering enforces a focus on content words, context-sensitive definitions, and example sentences tailored to definitions. The temperature parameter is set to 0.5 to balance creativity and determinism.

Sample prompts include:

- Translation prompt instructs extraction of content words, lemmatization, and translation, outputting unique lemma-to-translation mappings.
- Definition prompt instructs generating a single clear definition based on the original sentence context.
- Example prompt instructs generation of simple, clear example sentences matching the definition.

## 5. Retrieval-Augmented Generation (RAG)

Large LLM calls are computationally expensive and slow, so RAG is used to leverage existing vocabulary data for semantic similarity searches, reducing redundant calls and enhancing learner experience.

Vocabulary entries are embedded using the HuggingFace `all-MiniLM-L6-v2` model. FAISS indexes these embeddings for efficient nearest neighbor search. When processing a new word, the retriever queries for top-k similar words, incorporating these into the learner’s dictionary.

## 6. Persistent Storage

The vocabulary dictionary is saved as a JSON file mapping language pairs to word entries. Each entry contains lists of translations, definitions, and example sentences.

Example dictionary snippet:

```json
{
  "('en', 'ru')": {
    "run": {
      "translations": [""],
      "definitions": [""],
      "examples": [""]
    }
  }
}
```

## 7. Challenges Faced and Solutions

- Ensuring strict JSON output from the LLM was solved by using pydantic JSON parsers and robust error handling.

- Running a large LLM locally efficiently was achieved by using the quantized Gemma 3n model with Ollama.

- Generating context-specific definitions was addressed by carefully crafted prompts that use the sentence context and limit output to single definitions.

- Providing semantic similarity offline was realized by integrating FAISS with MiniLM embeddings.

- Avoiding duplicated processing was accomplished with a persistent dictionary and RAG retrieval.

- gemma3n is a multimodal large language model but unfortunatelly Ollama doesn't support any data type except text.

## Technical Decisions Justification

- LangGraph was chosen for its declarative, graph-based pipeline orchestration, improving modularity and maintainability.

- FAISS and MiniLM embeddings enable semantic search without internet access, critical for offline usability.

- JSON dictionary format offers human-readable, portable storage supporting downstream integrations.

- Prompt engineering ensures generated content fits educational goals: clarity, simplicity, and relevance.

## 9. Future Work

Planned improvements include extending support for additional input modalities like audio and images (using OCR and speech recognition), implementing an interactive UI for vocabulary review and quizzes, adding spaced repetition integration, fine-tuning Gemma 3n on learner-specific data for better personalization, and optimizing RAG retrieval speed and accuracy with hybrid search strategies.
