"""add hash indexes on words lemma

Revision ID: add_hash_indexes_lemma
Revises: 66a79084ba5f
Create Date: 2025-01-27 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_hash_indexes_lemma'
down_revision: Union[str, Sequence[str], None] = '66a79084ba5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add hash indexes on words lemma field."""
    
    # Create hash index on lemma field
    # Hash indexes are more efficient for exact equality comparisons
    # than B-tree indexes for string data
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_words_lemma_hash "
        "ON words USING hash (lemma)"
    )
    
    # Also create a composite B-tree index for lemma + language_id
    # This is useful for queries that filter by both lemma and language
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_words_lemma_language_btree "
        "ON words USING btree (lemma, language_id)"
    )
    
    # Create a functional hash index for lowercase lemma
    # This is useful for case-insensitive searches
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_words_lemma_lower_hash "
        "ON words USING hash (LOWER(lemma))"
    )


def downgrade() -> None:
    """Remove hash indexes on words lemma field."""
    
    # Drop the indexes in reverse order
    op.execute("DROP INDEX IF EXISTS idx_words_lemma_lower_hash")
    op.execute("DROP INDEX IF EXISTS idx_words_lemma_language_btree")
    op.execute("DROP INDEX IF EXISTS idx_words_lemma_hash")
