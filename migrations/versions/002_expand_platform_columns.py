"""Expand platforms table with all outreach tracking columns

Revision ID: 002
Revises: 001
Create Date: 2026-02-18

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('platforms', sa.Column('tier', sa.String(10)))
    op.add_column('platforms', sa.Column('submission_type', sa.String(50)))
    op.add_column('platforms', sa.Column('topic_to_submit', sa.String(300)))
    op.add_column('platforms', sa.Column('difficulty', sa.String(20)))
    op.add_column('platforms', sa.Column('pitch_sent_date', sa.Date()))
    op.add_column('platforms', sa.Column('article_sent_date', sa.Date()))
    op.add_column('platforms', sa.Column('follow_up_1', sa.Date()))
    op.add_column('platforms', sa.Column('follow_up_2', sa.Date()))
    op.add_column('platforms', sa.Column('response_date', sa.Date()))
    op.add_column('platforms', sa.Column('status', sa.String(50), server_default='Not Started'))
    op.add_column('platforms', sa.Column('publication_date', sa.Date()))
    op.add_column('platforms', sa.Column('live_url', sa.String(500)))
    op.add_column('platforms', sa.Column('backlink_confirmed', sa.Boolean(), server_default='false'))
    # Remove old domain_authority column (not in the new schema)
    op.drop_column('platforms', 'domain_authority')


def downgrade():
    op.add_column('platforms', sa.Column('domain_authority', sa.Integer()))
    op.drop_column('platforms', 'backlink_confirmed')
    op.drop_column('platforms', 'live_url')
    op.drop_column('platforms', 'publication_date')
    op.drop_column('platforms', 'status')
    op.drop_column('platforms', 'response_date')
    op.drop_column('platforms', 'follow_up_2')
    op.drop_column('platforms', 'follow_up_1')
    op.drop_column('platforms', 'article_sent_date')
    op.drop_column('platforms', 'pitch_sent_date')
    op.drop_column('platforms', 'difficulty')
    op.drop_column('platforms', 'topic_to_submit')
    op.drop_column('platforms', 'submission_type')
    op.drop_column('platforms', 'tier')
