--
-- PostgreSQL database dump
--

\restrict BMj7AZBKxMLUDx1blTqkZSk3AfTGSWlCyubmgexPO6eLpKgAPxsYcjGYT7ND3Hj

-- Dumped from database version 16.10 (Debian 16.10-1.pgdg12+1)
-- Dumped by pg_dump version 16.10 (Debian 16.10-1.pgdg12+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA public;


--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON SCHEMA public IS 'standard public schema';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: definitions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.definitions (
    id integer NOT NULL,
    definition_text text NOT NULL,
    language_id integer NOT NULL,
    dictionary_id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    embedding public.vector(384),
    embedding_model character varying(64),
    embedding_updated_at timestamp with time zone
);


--
-- Name: definitions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.definitions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: definitions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.definitions_id_seq OWNED BY public.definitions.id;


--
-- Name: dictionaries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dictionaries (
    id integer NOT NULL,
    learning_profile_id integer NOT NULL,
    word_id integer NOT NULL,
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: dictionaries_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dictionaries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dictionaries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dictionaries_id_seq OWNED BY public.dictionaries.id;


--
-- Name: examples; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.examples (
    id integer NOT NULL,
    language_id integer NOT NULL,
    dictionary_id integer NOT NULL,
    example_text text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    embedding public.vector(384),
    embedding_model character varying(64),
    embedding_updated_at timestamp with time zone
);


--
-- Name: examples_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.examples_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: examples_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.examples_id_seq OWNED BY public.examples.id;


--
-- Name: languages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.languages (
    id integer NOT NULL,
    code character(5),
    name character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: languages_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.languages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: languages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.languages_id_seq OWNED BY public.languages.id;


--
-- Name: learning_profiles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.learning_profiles (
    id integer NOT NULL,
    user_id integer NOT NULL,
    primary_language_id integer NOT NULL,
    foreign_language_id integer NOT NULL,
    is_active boolean,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT different_languages CHECK ((primary_language_id <> foreign_language_id))
);


--
-- Name: learning_profiles_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.learning_profiles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: learning_profiles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.learning_profiles_id_seq OWNED BY public.learning_profiles.id;


--
-- Name: texts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.texts (
    id integer NOT NULL,
    text text NOT NULL,
    learning_profile_id integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    embedding public.vector(384),
    embedding_model character varying(64),
    embedding_updated_at timestamp with time zone,
    dictionary_id integer
);


--
-- Name: texts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.texts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: texts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.texts_id_seq OWNED BY public.texts.id;


--
-- Name: translations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.translations (
    id integer NOT NULL,
    translation character varying NOT NULL,
    language_id integer NOT NULL,
    dictionary_id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    embedding public.vector(384),
    embedding_model character varying(64),
    embedding_updated_at timestamp with time zone
);


--
-- Name: translations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.translations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: translations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.translations_id_seq OWNED BY public.translations.id;


--
-- Name: user_word_progress; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_word_progress (
    id integer NOT NULL,
    learning_profile_id integer,
    word_id integer NOT NULL,
    proficiency integer,
    last_reviewed timestamp with time zone,
    next_review_due timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: user_word_progress_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_word_progress_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_word_progress_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_word_progress_id_seq OWNED BY public.user_word_progress.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying NOT NULL,
    password character varying NOT NULL,
    full_name character varying NOT NULL,
    email character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    disabled boolean NOT NULL
);


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: words; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.words (
    id integer NOT NULL,
    lemma character varying NOT NULL,
    language_id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    embedding public.vector(384),
    embedding_model character varying(64),
    embedding_updated_at timestamp with time zone
);


--
-- Name: words_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.words_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: words_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.words_id_seq OWNED BY public.words.id;


--
-- Name: definitions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.definitions ALTER COLUMN id SET DEFAULT nextval('public.definitions_id_seq'::regclass);


--
-- Name: dictionaries id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dictionaries ALTER COLUMN id SET DEFAULT nextval('public.dictionaries_id_seq'::regclass);


--
-- Name: examples id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.examples ALTER COLUMN id SET DEFAULT nextval('public.examples_id_seq'::regclass);


--
-- Name: languages id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.languages ALTER COLUMN id SET DEFAULT nextval('public.languages_id_seq'::regclass);


--
-- Name: learning_profiles id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning_profiles ALTER COLUMN id SET DEFAULT nextval('public.learning_profiles_id_seq'::regclass);


--
-- Name: texts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.texts ALTER COLUMN id SET DEFAULT nextval('public.texts_id_seq'::regclass);


--
-- Name: translations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.translations ALTER COLUMN id SET DEFAULT nextval('public.translations_id_seq'::regclass);


--
-- Name: user_word_progress id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_word_progress ALTER COLUMN id SET DEFAULT nextval('public.user_word_progress_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: words id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.words ALTER COLUMN id SET DEFAULT nextval('public.words_id_seq'::regclass);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: definitions definitions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.definitions
    ADD CONSTRAINT definitions_pkey PRIMARY KEY (id);


--
-- Name: dictionaries dictionaries_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dictionaries
    ADD CONSTRAINT dictionaries_pkey PRIMARY KEY (id);


--
-- Name: examples examples_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.examples
    ADD CONSTRAINT examples_pkey PRIMARY KEY (id);


--
-- Name: languages languages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.languages
    ADD CONSTRAINT languages_pkey PRIMARY KEY (id);


--
-- Name: learning_profiles learning_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning_profiles
    ADD CONSTRAINT learning_profiles_pkey PRIMARY KEY (id);


--
-- Name: texts texts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.texts
    ADD CONSTRAINT texts_pkey PRIMARY KEY (id);


--
-- Name: translations translations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.translations
    ADD CONSTRAINT translations_pkey PRIMARY KEY (id);


--
-- Name: user_word_progress uq_lprof_word; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_word_progress
    ADD CONSTRAINT uq_lprof_word UNIQUE (learning_profile_id, word_id);


--
-- Name: texts uq_user_text; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.texts
    ADD CONSTRAINT uq_user_text UNIQUE (learning_profile_id, text);


--
-- Name: user_word_progress user_word_progress_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_word_progress
    ADD CONSTRAINT user_word_progress_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: words words_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.words
    ADD CONSTRAINT words_pkey PRIMARY KEY (id);


--
-- Name: ix_definitions_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_definitions_id ON public.definitions USING btree (id);


--
-- Name: ix_dictionaries_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_dictionaries_id ON public.dictionaries USING btree (id);


--
-- Name: ix_examples_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_examples_id ON public.examples USING btree (id);


--
-- Name: ix_languages_code; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_languages_code ON public.languages USING btree (code);


--
-- Name: ix_languages_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_languages_id ON public.languages USING btree (id);


--
-- Name: ix_languages_name; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_languages_name ON public.languages USING btree (name);


--
-- Name: ix_learning_profiles_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_learning_profiles_id ON public.learning_profiles USING btree (id);


--
-- Name: ix_texts_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_texts_id ON public.texts USING btree (id);


--
-- Name: ix_translations_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_translations_id ON public.translations USING btree (id);


--
-- Name: ix_translations_translation; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_translations_translation ON public.translations USING btree (translation);


--
-- Name: ix_user_word_progress_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_word_progress_id ON public.user_word_progress USING btree (id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- Name: ix_users_username; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);


--
-- Name: ix_words_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_words_id ON public.words USING btree (id);


--
-- Name: ix_words_lemma; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_words_lemma ON public.words USING btree (lemma);


--
-- Name: definitions definitions_dictionary_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.definitions
    ADD CONSTRAINT definitions_dictionary_id_fkey FOREIGN KEY (dictionary_id) REFERENCES public.dictionaries(id);


--
-- Name: definitions definitions_language_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.definitions
    ADD CONSTRAINT definitions_language_id_fkey FOREIGN KEY (language_id) REFERENCES public.languages(id);


--
-- Name: dictionaries dictionaries_learning_profile_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dictionaries
    ADD CONSTRAINT dictionaries_learning_profile_id_fkey FOREIGN KEY (learning_profile_id) REFERENCES public.learning_profiles(id);


--
-- Name: dictionaries dictionaries_word_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dictionaries
    ADD CONSTRAINT dictionaries_word_id_fkey FOREIGN KEY (word_id) REFERENCES public.words(id);


--
-- Name: examples examples_dictionary_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.examples
    ADD CONSTRAINT examples_dictionary_id_fkey FOREIGN KEY (dictionary_id) REFERENCES public.dictionaries(id);


--
-- Name: examples examples_language_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.examples
    ADD CONSTRAINT examples_language_id_fkey FOREIGN KEY (language_id) REFERENCES public.languages(id);


--
-- Name: learning_profiles learning_profiles_foreign_language_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning_profiles
    ADD CONSTRAINT learning_profiles_foreign_language_id_fkey FOREIGN KEY (foreign_language_id) REFERENCES public.languages(id);


--
-- Name: learning_profiles learning_profiles_primary_language_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning_profiles
    ADD CONSTRAINT learning_profiles_primary_language_id_fkey FOREIGN KEY (primary_language_id) REFERENCES public.languages(id);


--
-- Name: learning_profiles learning_profiles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning_profiles
    ADD CONSTRAINT learning_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: texts texts_dictionary_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.texts
    ADD CONSTRAINT texts_dictionary_id_fkey FOREIGN KEY (dictionary_id) REFERENCES public.dictionaries(id);


--
-- Name: texts texts_learning_profile_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.texts
    ADD CONSTRAINT texts_learning_profile_id_fkey FOREIGN KEY (learning_profile_id) REFERENCES public.learning_profiles(id);


--
-- Name: translations translations_dictionary_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.translations
    ADD CONSTRAINT translations_dictionary_id_fkey FOREIGN KEY (dictionary_id) REFERENCES public.dictionaries(id);


--
-- Name: translations translations_language_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.translations
    ADD CONSTRAINT translations_language_id_fkey FOREIGN KEY (language_id) REFERENCES public.languages(id);


--
-- Name: user_word_progress user_word_progress_learning_profile_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_word_progress
    ADD CONSTRAINT user_word_progress_learning_profile_id_fkey FOREIGN KEY (learning_profile_id) REFERENCES public.learning_profiles(id);


--
-- Name: user_word_progress user_word_progress_word_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_word_progress
    ADD CONSTRAINT user_word_progress_word_id_fkey FOREIGN KEY (word_id) REFERENCES public.words(id);


--
-- Name: words words_language_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.words
    ADD CONSTRAINT words_language_id_fkey FOREIGN KEY (language_id) REFERENCES public.languages(id);


--
-- PostgreSQL database dump complete
--

\unrestrict BMj7AZBKxMLUDx1blTqkZSk3AfTGSWlCyubmgexPO6eLpKgAPxsYcjGYT7ND3Hj

