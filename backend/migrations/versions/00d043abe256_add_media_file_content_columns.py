"""add_media_file_content_columns

Revision ID: 00d043abe256
Revises: webhook_fields_migration
Create Date: 2025-08-08 17:09:30.500437

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '00d043abe256'
down_revision = 'webhook_fields_migration'
branch_labels = None
depends_on = None


def upgrade():
    # Define schema
    schema = 'getinn_ops'
    
    # First add the new columns
    op.add_column('bot_media_file', sa.Column('file_content', sa.LargeBinary(), nullable=True), schema=schema)
    op.add_column('bot_media_file', sa.Column('content_type', sa.String(), nullable=True), schema=schema)
    op.add_column('bot_media_file', sa.Column('file_size', sa.Integer(), nullable=True), schema=schema)
    
    # Add SQL to populate the new columns with default values for existing records
    op.execute(f'''
    UPDATE {schema}.bot_media_file 
    SET 
        file_content = decode('89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C4890000000D4944415478DAE3626000000006000105D4378F0000000049454E44AE426082', 'hex'),
        content_type = 'application/octet-stream',
        file_size = 67
    WHERE file_content IS NULL
    ''')
    
    # Make the columns non-nullable once populated with default values
    op.alter_column('bot_media_file', 'file_content', nullable=False, schema=schema)
    op.alter_column('bot_media_file', 'content_type', nullable=False, schema=schema)
    op.alter_column('bot_media_file', 'file_size', nullable=False, schema=schema)
    
    # Then completely remove the legacy storage_path column
    op.drop_column('bot_media_file', 'storage_path', schema=schema)


def downgrade():
    # Define schema
    schema = 'getinn_ops'
    
    # Add back the storage_path column
    op.add_column('bot_media_file', sa.Column('storage_path', sa.String(), nullable=True), schema=schema)
    
    # Drop the columns we added in the upgrade
    op.drop_column('bot_media_file', 'file_size', schema=schema)
    op.drop_column('bot_media_file', 'content_type', schema=schema)
    op.drop_column('bot_media_file', 'file_content', schema=schema)