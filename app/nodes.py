from app.generate import generate_translation, generate_definition, generate_examples, codes_language, language_codes
from langgraph.graph import StateGraph, START, END
from app.schemas import State, AllRead

def translate_words_node(state: State) -> dict:
    """
    Node: Translate words from source language to target language.

    This function:
    1. Calls `generate_translation()` to translate the input text.
    2. Extracts the set of words from the translation keys.
    3. Returns updated `words` and `translations` in the state.

    Args:
        state (State): Current state containing `text`, `src_language`, and `tgt_language`.

    Returns:
        dict: Updated state keys:
            - 'words': set of unique words found in translation
            - 'translations': dict with translations
    """
    translations = generate_translation(
        text=state["text"],
        src_language=codes_language[state['src_language']],  # Convert to language code
        tgt_language=codes_language[state['tgt_language']]
    )

    # Extract words from translation keys
    words = set(translations.keys())

    return {
        'words': words,
        'translations': translations
    }

def generate_definitions_node(state: State) -> dict:
    """
    Node: Generate definitions for translated words.

    This function:
    1. Iterates over existing words in `definitions`.
    2. Calls `generate_definitions()` for each word.
    3. Extends the definitions list if new ones are found.

    Args:
        state (State): Current state containing `definitions` and `src_language`.

    Returns:
        dict: Updated 'definitions' key in state.
    """
    definitions = state['definitions']

    for word in list(definitions.keys()):  # Copy keys to avoid runtime mutation issues
        def_dict = generate_definition(
            word,
            codes_language[state['src_language']]
        )

        # Append new definitions if they exist
        if def_dict.get('definition'):
            definitions[word].extend(def_dict['definition'])

    return {'definitions': definitions}

def generate_examples_node(state: State) -> dict:
    """
    Node: Generate example sentences for each word.

    This function:
    1. Uses `examples_number` to determine how many examples per word.
    2. Calls `generate_examples()` for each word.
    3. Extends the examples list if new ones are found.

    Args:
        state (State): Current state containing `examples`, `examples_number`, `definitions`.

    Returns:
        dict: Updated 'examples' key in state.
    """
    examples = state['examples']

    for word in examples.keys():

        ex_number = 1


        if state['examples_number'].get(word):
            ex_number = state['examples_number'][word]

        ex_dict = generate_examples(
            word,
            codes_language[state['src_language']],
            state['definitions'][word],
            ex_number
        )

        # Append examples if found
        if ex_dict.get('examples'):
            examples[word].extend(ex_dict['examples'])

    return {
        'examples': examples
    }



