"""Initial schema: platforms, targets, campaigns, outreach_emails

Revision ID: 001
Revises:
Create Date: 2026-02-17

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'platforms',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('url', sa.String(500), nullable=False),
        sa.Column('domain_authority', sa.Integer()),
        sa.Column('contact_email', sa.String(200)),
        sa.Column('contact_name', sa.String(200)),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        'campaigns',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('status', sa.String(50), server_default='draft'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        'targets',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('platform_id', sa.Integer(),
                  sa.ForeignKey('platforms.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_url', sa.String(500), nullable=False),
        sa.Column('target_page_title', sa.String(300)),
        sa.Column('our_url', sa.String(500)),
        sa.Column('anchor_text', sa.String(300)),
        sa.Column('status', sa.String(50), server_default='identified', nullable=False),
        sa.Column('priority', sa.String(20), server_default='medium'),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        'outreach_emails',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('target_id', sa.Integer(),
                  sa.ForeignKey('targets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('campaign_id', sa.Integer(),
                  sa.ForeignKey('campaigns.id', ondelete='CASCADE'), nullable=True),
        sa.Column('recipient_email', sa.String(200), nullable=False),
        sa.Column('subject', sa.String(500), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('status', sa.String(50), server_default='draft'),
        sa.Column('sent_at', sa.DateTime()),
        sa.Column('gmail_message_id', sa.String(200)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table('outreach_emails')
    op.drop_table('targets')
    op.drop_table('campaigns')
    op.drop_table('platforms')
