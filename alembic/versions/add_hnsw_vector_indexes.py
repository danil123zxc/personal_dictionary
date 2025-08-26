"""add hnsw vector indexes

Revision ID: add_hnsw_vector_indexes
Revises: 66a79084ba5f
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = 'add_hnsw_vector_indexes'
down_revision = '66a79084ba5f'
branch_labels = None
depends_on = None


def upgrade():
    # Create HNSW index for words.embedding with cosine distance
    # Note: CONCURRENTLY cannot run in transaction, so we use regular CREATE INDEX
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_words_embedding_hnsw 
        ON words USING hnsw (embedding vector_cosine_ops) 
        WITH (m = 16, ef_construction = 200)
    """)
    
    # Create additional indexes for filtering performance
    op.create_index('idx_words_language_id', 'words', ['language_id'])
    op.create_index('idx_dictionaries_learning_profile_id', 'dictionaries', ['learning_profile_id'])
    op.create_index('idx_dictionaries_word_id', 'dictionaries', ['word_id'])


def downgrade():
    # Drop indexes in reverse order
    op.drop_index('idx_dictionaries_word_id', table_name='dictionaries')
    op.drop_index('idx_dictionaries_learning_profile_id', table_name='dictionaries')
    op.drop_index('idx_words_language_id', table_name='words')
    op.execute("DROP INDEX IF EXISTS idx_words_embedding_hnsw")
