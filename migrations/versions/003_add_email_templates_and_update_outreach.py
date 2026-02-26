"""Add email_templates table and update outreach_emails with platform/template links

Revision ID: 003
Revises: 002
Create Date: 2026-02-26

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # Create email_templates table
    op.create_table(
        'email_templates',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('subject', sa.String(500), nullable=False),
        sa.Column('body_html', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

    # Add new columns to outreach_emails
    op.add_column('outreach_emails', sa.Column('platform_id', sa.Integer(), nullable=True))
    op.add_column('outreach_emails', sa.Column('template_id', sa.Integer(), nullable=True))

    op.create_foreign_key('fk_email_platform', 'outreach_emails', 'platforms',
                          ['platform_id'], ['id'])
    op.create_foreign_key('fk_email_template', 'outreach_emails', 'email_templates',
                          ['template_id'], ['id'])

    # Make target_id nullable (bulk sends go directly to platform contacts)
    op.alter_column('outreach_emails', 'target_id', nullable=True)


def downgrade():
    op.alter_column('outreach_emails', 'target_id', nullable=False)
    op.drop_constraint('fk_email_template', 'outreach_emails', type_='foreignkey')
    op.drop_constraint('fk_email_platform', 'outreach_emails', type_='foreignkey')
    op.drop_column('outreach_emails', 'template_id')
    op.drop_column('outreach_emails', 'platform_id')
    op.drop_table('email_templates')
