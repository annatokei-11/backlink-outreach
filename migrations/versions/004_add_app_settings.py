"""Add app_settings table for storing API keys in the database

Revision ID: 004
Revises: 003
Create Date: 2026-02-26

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'app_settings',
        sa.Column('key', sa.String(100), primary_key=True),
        sa.Column('value', sa.Text(), nullable=False, server_default=''),
    )


def downgrade():
    op.drop_table('app_settings')
