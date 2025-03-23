"""create user and note tables

Revision ID: 7f5baddaa615
Revises: 
Create Date: 2025-03-23 17:49:14.891673

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '7f5baddaa615'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if tables exist before creating them
    inspector = sa.inspect(op.get_bind())
    existing_tables = inspector.get_table_names()
    
    if 'user' not in existing_tables:
        op.create_table('user',
            sa.Column('email', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('first_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('last_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('birthdate', sa.DateTime(), nullable=True),
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('hashed_password', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)
    
    if 'note' not in existing_tables:
        op.create_table('note',
            sa.Column('text', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('summary', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('embedding', sa.JSON(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
            sa.PrimaryKeyConstraint('id')
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('note')
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_table('user')
