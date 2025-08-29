from src.services.generate import generate_translation, generate_definition, generate_examples, codes_language, language_codes
from langgraph.graph import StateGraph, START, END
from src.models.schemas import State, AllRead, Context
from src.models.models import PartOfSpeech
from src.services.crud import get_learning_profile, get_language_id, get_synonyms, create_word, create_in_dictionary, create_translation, create_definition, create_example, create_text
from src.models.models import Word, Dictionary, LearningProfile
from sqlalchemy.orm import Session
from fastapi import HTTPException
from src.models.crud_schemas import LearningProfileRead, TextRead, WordBase, DictionaryBase, TranslationBase, DictionaryRead, DefinitionBase, ExampleBase, DefinitionRead, ExampleRead, TranslationRead
from langchain.tools import tool
from langgraph.prebuilt import ToolNode
import spacy
import pymorphy2
from konlpy.tag import Mecab
from typing import List, Dict, TypedDict, Tuple, Set
from langchain_text_splitters import RecursiveCharacterTextSplitter

_KO_OKT_TO_UPOS = {
    "Noun": "NOUN",
    "Verb": "VERB",
    "Adjective": "ADJ",
    "Adverb": "ADV",
    "Determiner": "DET",
    "Conjunction": "CCONJ",
    "Exclamation": "INTJ",
    "Josa": "PART",        # could be ADP in strict UD; PART is fine for search/normalization
    "Eomi": "PART",        # endings
    "PreEomi": "PART",
    "Suffix": "PART",
    "NounPrefix": "X",
    "VerbPrefix": "X",
    "Number": "NUM",
    "Foreign": "X",
    "Alpha": "X",
    "Punctuation": "PUNCT",
    "KoreanParticle": "PART",  # sometimes used
}

_RU_TO_UPOS = {
    "NOUN": "NOUN",
    "ADJF": "ADJ",    # full adjective
    "ADJS": "ADJ",    # short adjective
    "COMP": "ADJ",    # comparative; could be ADV sometimes
    "VERB": "VERB",   # finite verb
    "INFN": "VERB",   # infinitive
    "PRTF": "VERB",   # participle (treat as VERB; optionally ADJ if used attributively)
    "PRTS": "VERB",   # short participle
    "GRND": "VERB",   # gerund
    "NUMR": "NUM",
    "ADVB": "ADV",
    "NPRO": "PRON",
    "PRED": "ADV",    # predicative; could be ADJ; we choose ADV as fallback
    "PREP": "ADP",    # preposition
    "CONJ": "CCONJ",  # can be SCONJ in some contexts; simple mapping to CCONJ
    "PRCL": "PART",
    "INTJ": "INTJ",
}

def lemmatize_text(text: str, lang: str) -> Dict[str, Set[Tuple[str, str, str]]]:
    """
    Lemmatize text depending on language with context preservation.
    Supports: English, Russian, Korean.
    
    Returns dict: {chunk_text: {("lemma", "pos", "lang"), ...}}
    """ 
    results = {}

    # Split text into chunks for context preservation
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300, 
        chunk_overlap=100, 
        add_start_index=True,
        separators=["\n\n", "\n", ".", "!", "?", ", ", " ", ""]
    )
    chunks = text_splitter.split_text(text) # type: ignore  
    
    # Process each chunk
    for chunk in chunks:
        chunk_words = set()
        
        if lang == "en":
            try:
                nlp = spacy.load("en_core_web_sm")
                doc = nlp(chunk)
                for token in doc:
                    if token.is_alpha:
                        chunk_words.add((token.lemma_, token.pos_, lang))
            except OSError:
                # Fallback to simple splitting
                words = chunk.split()
                for word in words:
                    if word.isalpha():
                        chunk_words.add((word.lower(), "X", lang))

        # Russian (better accuracy with pymorphy2)
        elif lang == "ru":
            try:
                morph_ru = pymorphy2.MorphAnalyzer()
                tokens = chunk.split()  
                for token in tokens:
                    if token.isalpha():
                        parsed = morph_ru.parse(token)[0]
                        chunk_words.add((parsed.normal_form, _RU_TO_UPOS[parsed.tag.POS], lang))
            except Exception:
                # Fallback
                words = chunk.split()
                for word in words:
                    if word.isalpha():
                        chunk_words.add((word.lower(), "X", lang))

        # Korean (Mecab)
        elif lang == "ko":
            try:
                mecab = Mecab()
                for token, pos in mecab.pos(chunk):
                    chunk_words.add((token, _KO_OKT_TO_UPOS[pos], lang))
            except Exception:
                # Fallback
                words = chunk.split()
                for word in words:
                    chunk_words.add((word, "X", lang))

        else:
            # Fallback for unsupported languages
            words = chunk.split()
            for word in words:
                if word.isalpha():
                    chunk_words.add((word.lower(), "X", lang))
        
        # Add chunk with its words
        if chunk_words:
            results[chunk] = chunk_words
    return results

def extract_saved_words_node(state: State, context: Context) -> dict:
    """
    Extract words from saved text that are not already in user's dictionary.
    Returns words that need to be created with their context chunks.
    
    Returns: {"chunks": {chunk_text: {("lemma", "pos", "lang"), ...}}}
    """
    chunks = lemmatize_text(state['text'], context.primary_language)
    db = context.db
    words_to_create = {}  
    
    # Process each chunk and its words
    for chunk_text, chunk_words in chunks.items():
        words_to_create[chunk_text] = set()
        for lemma, pos, lang in chunk_words:
            # Convert string POS to enum if needed
            pos_enum = None
            if isinstance(pos, str):
                try:
                    pos_enum = PartOfSpeech(pos)
                except ValueError:
                    pos_enum = None
            
            # Check if word exists in user's dictionary
            word_exists = db.query(
                db.query(Word.id)
                .join(Dictionary, Word.id == Dictionary.word_id)
                .join(LearningProfile, Dictionary.learning_profile_id == LearningProfile.id)
                .filter(
                    LearningProfile.id == context.learning_profile_id,
                    Word.lemma == lemma,  
                    Word.pos == pos_enum, 
                )
                .exists()
            ).scalar()
            
            # If word doesn't exist in dictionary, add it to creation list
            if not word_exists:
                words_to_create[chunk_text].add((lemma, pos, lang))
    
    return {"chunks": words_to_create}

def translate_words_node(state: State) -> dict:
    """
    Node: Translate words from source language to target language.

    This function:
    1. Processes chunks with words that need translation.
    2. Calls `generate_translation()` for each chunk with context.
    3. Tracks already translated words to avoid duplicates.
    4. Returns updated `words` and `translations` in the state.

    Args:
        state (State): Current state containing `chunks`, `src_language`, and `tgt_language`.

    Returns:
        dict: Updated state keys:
            - 'words': set of unique words found in translation
            - 'translations': dict with translations
    """
    translations = {}
    chunks = state['chunks']
    chunk_list = list(chunks.items())  # Convert to list for indexing
    already_translated = set()  # Track words already translated
    
    for i, (chunk_text, chunk_words) in enumerate(chunk_list):
        # Extract just the lemmas for translation, excluding already translated ones
        words_to_translate = []
        for lemma, pos, lang in chunk_words:
            if lemma not in already_translated:
                words_to_translate.append(lemma)
                already_translated.add(lemma)
        
        # Skip if no new words to translate
        if not words_to_translate:
            continue
        
        # Create context: current chunk + next overlapping chunk
        context = chunk_text
        if i + 1 < len(chunk_list):
            next_chunk_text = chunk_list[i + 1][0]
            context = f"{chunk_text} {next_chunk_text}"

        # Call generate_translation for this chunk
        chunk_translation = generate_translation(
            context=context,
            words=words_to_translate,
            src_language=codes_language[state['src_language']],  
            tgt_language=codes_language[state['tgt_language']]
        )
        translations.update(chunk_translation)
        
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

@tool
def save_text_node(state: State, context: Context) -> dict:
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

@tool
def save_words_node(state: State, context: Context) -> dict:
    """
    Node: Save words to the database.
    """
    
    db = context.db

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
    

@tool
def save_dictionary_node(state: State, context: Context) -> dict:
    """
    Node: Save dictionary entries to the database.
    """
    
    db = context.db

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


@tool
def save_translation_node(state: State, context: Context) -> dict:
    """
    Node: Save translations to the database.
    """
    
    db = context.db

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
  

@tool
def save_definition_node(state: State, context: Context) -> dict:
    """
    Node: Save definitions to the database.
    """
    
    db = context.db

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

@tool
def save_example_node(state: State, context: LearningProfileRead) -> dict:
    """
    Node: Save examples to the database.
    """
 
    
    db = context.db

    src_language_id = get_language_id(language_name=context.primary_language)
    dictionary_db_map = state.get('dictionary_db_map', {})
    created_examples = []

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

save_words_node = ToolNode([
    save_words_node,
    save_text_node,
    save_dictionary_node,
    save_translation_node,
    save_definition_node,
    save_example_node
])

graph = StateGraph(State, context=LearningProfileRead)
graph.add_node("extract_saved_words", extract_saved_words_node)
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

graph.add_edge(START, "extract_saved_words")
graph.add_edge("extract_saved_words", "translate_words")
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

# Conditional edges for save_example node
graph.add_conditional_edges(
    "save_example",
    lambda x: "created_examples" if x.get("created_examples") else "failed_examples",
    {
        "created_examples": END,
        "failed_examples": END
    }
)


