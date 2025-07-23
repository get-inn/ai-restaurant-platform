"""Add webhook fields to bot platform credential

Revision ID: webhook_fields_migration
Revises: initial_migration
Create Date: 2025-07-23 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'webhook_fields_migration'
down_revision = 'initial_migration'
branch_labels = None
depends_on = None


def upgrade():
    # Add webhook-related fields to bot_platform_credential
    op.add_column('bot_platform_credential', sa.Column('webhook_url', sa.String(), nullable=True), schema='getinn_ops')
    op.add_column('bot_platform_credential', sa.Column('webhook_last_checked', sa.DateTime(), nullable=True), schema='getinn_ops')
    op.add_column('bot_platform_credential', sa.Column('webhook_auto_refresh', sa.Boolean(), nullable=False, server_default='true'), schema='getinn_ops')


def downgrade():
    # Remove webhook-related fields from bot_platform_credential
    op.drop_column('bot_platform_credential', 'webhook_auto_refresh', schema='getinn_ops')
    op.drop_column('bot_platform_credential', 'webhook_last_checked', schema='getinn_ops')
    op.drop_column('bot_platform_credential', 'webhook_url', schema='getinn_ops')