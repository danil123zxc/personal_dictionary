"""add pos enum to words

Revision ID: add_pos_enum_to_words
Revises: add_hash_indexes_lemma
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_pos_enum_to_words'
down_revision = 'add_hash_indexes_lemma'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create the enum type
    pos_enum = postgresql.ENUM('NOUN', 'VERB', 'ADJ', 'ADV', 'PRON', 'DET', 'ADP', 'NUM', 'CONJ', 'PART', 'INTJ', 'PUNCT', 'X', name='partofspeech')
    pos_enum.create(op.get_bind())
    
    # Add the column with the enum type
    op.add_column('words', sa.Column('pos', pos_enum, nullable=True))

def downgrade() -> None:
    # Drop the column
    op.drop_column('words', 'pos')
    
    # Drop the enum type
    pos_enum = postgresql.ENUM(name='partofspeech')
    pos_enum.drop(op.get_bind())
