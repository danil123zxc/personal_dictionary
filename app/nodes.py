from app.generate import generate_translation, generate_definition, generate_examples, codes_language, language_codes
from langgraph.graph import StateGraph, START, END
from app.schemas import State, AllRead
from app.crud import get_learning_profile, get_language_id, get_synonyms, create_word, create_in_dictionary, create_translation, create_definition, create_example, create_text
from app.models import Word, Dictionary
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.crud_schemas import LearningProfileRead, TextRead, WordBase, DictionaryBase, TranslationBase, DictionaryRead, DefinitionBase, ExampleBase, DefinitionRead, ExampleRead, TranslationRead

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

def get_synonyms_node(state: State) -> dict:
    """
    Node: Get synonyms for each word.

    This function:
    1. Iterates over existing words in `synonyms`.
    2. Calls `get_synonyms()` for each word.
    3. Extends the synonyms list if new ones are found.


    Args:
        state (State): Current state containing `synonyms` and `src_language`.

    Returns:
        dict: Updated 'synonyms' key in state.
    """
    synonyms = state['synonyms']    

    for word in synonyms.keys():
        synonyms[word] = get_synonyms(
            word,
            codes_language[state['src_language']]
        )

    return {'synonyms': synonyms}

def save_text_node(state: State, context: LearningProfileRead) -> dict:
    """
    Node: Save the input text to the database.
    """

    
    db = context.db

    src_language_id = context.primary_language_id
    tgt_language_id = context.foreign_language_id
    learning_profile_id = context.learning_profile_id
    try:
        text: TextRead = create_text(db, state['text'], learning_profile_id, src_language_id, tgt_language_id)
        return state
    except Exception as e:
        return state


def save_words_node(state: State, context: LearningProfileRead) -> dict:
    """
    Node: Save words to the database.
    """
    from app.database import SessionLocal
    
    db = SessionLocal()
    try:
        src_language_id = get_language_id(language_name=context.primary_language)
        created_words = []
        existing_words = []
        word_db_map = {}  # Map words to their database objects
        
        for word in state['words']:
            try:
                current_word = WordBase(lemma=word, language_id=src_language_id)
                word_db = create_word(db, current_word)
                created_words.append(word)
                word_db_map[word] = word_db
            except HTTPException as e:
                if e.status_code == 409:  # Word already exists
                    word_db = db.query(Word).filter(
                        Word.lemma == word,
                        Word.language_id == src_language_id
                    ).first()
                    existing_words.append(word)
                    word_db_map[word] = word_db
                else:
                    print(f"Error creating word '{word}': {e}")
                    continue
        
        return {
            'created_words': created_words,
            'existing_words': existing_words,
            'word_db_map': word_db_map
        }
    finally:
        db.close()

def save_dictionary_node(state: State, context: LearningProfileRead) -> dict:
    """
    Node: Save dictionary entries to the database.
    """
    from app.database import SessionLocal
    
    db = SessionLocal()
    try:
        learning_profile_id = context.learning_profile_id
        word_db_map = state.get('word_db_map', {})
        created_dictionary_entries = []
        existing_dictionary_entries = []
        dictionary_db_map = {}  # Map words to their dictionary objects
        
        for word, word_db in word_db_map.items():
            try:
                dictionary = DictionaryBase(learning_profile_id=learning_profile_id, word_id=word_db.id)
                dictionary_db = create_in_dictionary(db, dictionary, context.user)
                created_dictionary_entries.append(word)
                dictionary_db_map[word] = dictionary_db
            except HTTPException as e:
                if e.status_code == 409:  # Dictionary entry already exists
                    dictionary_db = db.query(Dictionary).filter(
                        Dictionary.learning_profile_id == learning_profile_id,
                        Dictionary.word_id == word_db.id
                    ).first()
                    existing_dictionary_entries.append(word)
                    dictionary_db_map[word] = dictionary_db
                else:
                    print(f"Error creating dictionary entry for word '{word}': {e}")
                    continue
        
        return {
            'created_dictionary_entries': created_dictionary_entries,
            'existing_dictionary_entries': existing_dictionary_entries,
            'dictionary_db_map': dictionary_db_map
        }
    finally:
        db.close()

def save_translation_node(state: State, context: LearningProfileRead) -> dict:
    """
    Node: Save translations to the database.
    """
    from app.database import SessionLocal
    
    db = SessionLocal()
    try:
        src_language_id = get_language_id(language_name=context.primary_language)
        dictionary_db_map = state.get('dictionary_db_map', {})
        created_translations = []
        failed_translations = []
        
        for word, dictionary_db in dictionary_db_map.items():
            try:
                translation = TranslationBase(
                    translation=state['translations'][word], 
                    language_id=src_language_id, 
                    dictionary_id=dictionary_db.id
                )
                translation_db = create_translation(db, translation, context.user)
                created_translations.append(word)
            except Exception as e:
                print(f"Error creating translation for word '{word}': {e}")
                failed_translations.append(word)
                continue
        
        return {
            'created_translations': created_translations,
            'failed_translations': failed_translations
        }
    finally:
        db.close()

def save_definition_node(state: State, context: LearningProfileRead) -> dict:
    """
    Node: Save definitions to the database.
    """
    from app.database import SessionLocal
    
    db = SessionLocal()
    try:
        src_language_id = get_language_id(language_name=context.primary_language)
        dictionary_db_map = state.get('dictionary_db_map', {})
        created_definitions = []
        failed_definitions = []
        
        for word, dictionary_db in dictionary_db_map.items():
            try:
                definition = DefinitionBase(
                    dictionary_id=dictionary_db.id, 
                    language_id=src_language_id, 
                    definition_text=state['definitions'][word]
                )
                definition_db = create_definition(db, definition, context.user)
                created_definitions.append(word)
            except Exception as e:
                print(f"Error creating definition for word '{word}': {e}")
                failed_definitions.append(word)
                continue
        
        return {
            'created_definitions': created_definitions,
            'failed_definitions': failed_definitions
        }
    finally:
        db.close()

def save_example_node(state: State, context: LearningProfileRead) -> dict:
    """
    Node: Save examples to the database.
    """
 
    
    db = context.db

    src_language_id = get_language_id(language_name=context.primary_language)
    dictionary_db_map = state.get('dictionary_db_map', {})
    created_examples = []
    failed_examples = []
    
    for word, dictionary_db in dictionary_db_map.items():
        try:
            example = ExampleBase(
                dictionary_id=dictionary_db.id, 
                language_id=src_language_id, 
                example_text=state['examples'][word]
            )
            example_db = create_example(db, example, context.user)
            created_examples.append(word)
        except Exception as e:
            continue
    
    return {
        'created_examples': created_examples
    }


graph = StateGraph(State, context=LearningProfileRead)
graph.add_node("translate_words", translate_words_node)
graph.add_node("generate_definitions", generate_definitions_node)
graph.add_node("generate_examples", generate_examples_node)
graph.add_node("get_synonyms", get_synonyms_node)
graph.add_node("save_text", save_text_node)
graph.add_node("save_words", save_words_node)
graph.add_node("save_dictionary", save_dictionary_node)
graph.add_node("save_translation", save_translation_node)
graph.add_node("save_definition", save_definition_node)
graph.add_node("save_example", save_example_node)

graph.add_edge(START, "translate_words")
graph.add_edge("translate_words", "generate_definitions")
graph.add_edge("generate_definitions", "generate_examples")
graph.add_edge("generate_examples", "get_synonyms")
graph.add_edge("get_synonyms", "save_text")
graph.add_edge("save_text", "save_words")
graph.add_edge("save_words", "save_dictionary")
graph.add_edge("save_dictionary", "save_translation")
graph.add_edge("save_translation", "save_definition")
graph.add_edge("save_definition", "save_example")
graph.add_edge("save_example", END)

graph.add_conditional_edges(
    "save_example",
    {
        "created_examples": "save_example",
        "failed_examples": "save_example"
    }
)


