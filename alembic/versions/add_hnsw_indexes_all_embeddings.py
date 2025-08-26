"""add hnsw indexes all embeddings

Revision ID: add_hnsw_indexes_all_embeddings
Revises: add_hnsw_vector_indexes
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = 'add_hnsw_indexes_all_embeddings'
down_revision = 'add_hnsw_vector_indexes'
branch_labels = None
depends_on = None


def upgrade():
    # Create HNSW indexes for all tables with embedding columns
    
    # Definitions table
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_definitions_embedding_hnsw 
        ON definitions USING hnsw (embedding vector_cosine_ops) 
        WITH (m = 16, ef_construction = 200)
    """)
    
    # Examples table
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_examples_embedding_hnsw 
        ON examples USING hnsw (embedding vector_cosine_ops) 
        WITH (m = 16, ef_construction = 200)
    """)
    
    # Translations table
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_translations_embedding_hnsw 
        ON translations USING hnsw (embedding vector_cosine_ops) 
        WITH (m = 16, ef_construction = 200)
    """)
    
    # Text chunks table
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_text_chunks_embedding_hnsw 
        ON text_chunks USING hnsw (embedding vector_cosine_ops) 
        WITH (m = 16, ef_construction = 200)
    """)
    
    # Create additional filtering indexes for performance
    op.create_index('idx_definitions_language_id', 'definitions', ['language_id'])
    op.create_index('idx_definitions_dictionary_id', 'definitions', ['dictionary_id'])
    op.create_index('idx_examples_language_id', 'examples', ['language_id'])
    op.create_index('idx_examples_dictionary_id', 'examples', ['dictionary_id'])
    op.create_index('idx_translations_language_id', 'translations', ['language_id'])
    op.create_index('idx_translations_dictionary_id', 'translations', ['dictionary_id'])
    op.create_index('idx_text_chunks_text_id', 'text_chunks', ['text_id'])
    op.create_index('idx_text_chunks_learning_profile_id', 'text_chunks', ['learning_profile_id'])


def downgrade():
    # Drop indexes in reverse order
    op.drop_index('idx_text_chunks_learning_profile_id', table_name='text_chunks')
    op.drop_index('idx_text_chunks_text_id', table_name='text_chunks')
    op.drop_index('idx_translations_dictionary_id', table_name='translations')
    op.drop_index('idx_translations_language_id', table_name='translations')
    op.drop_index('idx_examples_dictionary_id', table_name='examples')
    op.drop_index('idx_examples_language_id', table_name='examples')
    op.drop_index('idx_definitions_dictionary_id', table_name='definitions')
    op.drop_index('idx_definitions_language_id', table_name='definitions')
    
    # Drop HNSW indexes
    op.execute("DROP INDEX IF EXISTS idx_text_chunks_embedding_hnsw")
    op.execute("DROP INDEX IF EXISTS idx_translations_embedding_hnsw")
    op.execute("DROP INDEX IF EXISTS idx_examples_embedding_hnsw")
    op.execute("DROP INDEX IF EXISTS idx_definitions_embedding_hnsw")
