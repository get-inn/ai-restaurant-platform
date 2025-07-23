"""Initial migration with getinn_ops schema

Revision ID: initial_migration
Revises: 
Create Date: 2025-06-28 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid
import os

# revision identifiers, used by Alembic.
revision = 'initial_migration'
down_revision = None
branch_labels = None
depends_on = None

# Get schema name from environment
database_schema = os.getenv("DATABASE_SCHEMA", "getinn_ops")

def upgrade():
    # Create schema if it doesn't exist
    op.execute(f'CREATE SCHEMA IF NOT EXISTS {database_schema}')
    
    # Create tables
    # Core entities
    op.create_table('account',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()'), onupdate=sa.text('now()')),
        schema=database_schema
    )

    op.create_table('restaurant',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()'), onupdate=sa.text('now()')),
        # External system integration fields
        sa.Column('external_id', sa.String(), nullable=True),
        sa.Column('external_sync_status', sa.String(), nullable=True),
        sa.Column('external_system_type', sa.String(), nullable=True),
        sa.Column('external_last_synced_at', sa.DateTime(), nullable=True),
        sa.Column('external_sync_error', sa.String(), nullable=True),
        sa.Column('external_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['account_id'], [f'{database_schema}.account.id'], ),
        schema=database_schema
    )

    op.create_table('store',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('restaurant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()'), onupdate=sa.text('now()')),
        # External system integration fields
        sa.Column('external_id', sa.String(), nullable=True),
        sa.Column('external_sync_status', sa.String(), nullable=True),
        sa.Column('external_system_type', sa.String(), nullable=True),
        sa.Column('external_last_synced_at', sa.DateTime(), nullable=True),
        sa.Column('external_sync_error', sa.String(), nullable=True),
        sa.Column('external_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['restaurant_id'], [f'{database_schema}.restaurant.id'], ),
        schema=database_schema
    )

    op.create_table('supplier',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('contact_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()'), onupdate=sa.text('now()')),
        # External system integration fields
        sa.Column('external_id', sa.String(), nullable=True),
        sa.Column('external_sync_status', sa.String(), nullable=True),
        sa.Column('external_system_type', sa.String(), nullable=True),
        sa.Column('external_last_synced_at', sa.DateTime(), nullable=True),
        sa.Column('external_sync_error', sa.String(), nullable=True),
        sa.Column('external_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['account_id'], [f'{database_schema}.account.id'], ),
        schema=database_schema
    )

    op.create_table('user_profile',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('restaurant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.ForeignKeyConstraint(['account_id'], [f'{database_schema}.account.id'], ),
        sa.ForeignKeyConstraint(['restaurant_id'], [f'{database_schema}.restaurant.id'], ),
        schema=database_schema
    )

    # Units and measurements
    op.create_table('unit_category',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        schema=database_schema
    )

    op.create_table('unit',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('unit_category_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['account_id'], [f'{database_schema}.account.id'], ),
        sa.ForeignKeyConstraint(['unit_category_id'], [f'{database_schema}.unit_category.id'], ),
        schema=database_schema
    )

    op.create_table('unit_conversion',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('from_unit_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('to_unit_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversion_factor', sa.Numeric(precision=12, scale=6), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['from_unit_id'], [f'{database_schema}.unit.id'], ),
        sa.ForeignKeyConstraint(['to_unit_id'], [f'{database_schema}.unit.id'], ),
        schema=database_schema
    )

    # Inventory management
    op.create_table('inventory_item',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('sku', sa.String(), nullable=True),
        sa.Column('default_unit_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('item_type', sa.String(), nullable=True),
        sa.Column('current_cost_per_unit', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('reorder_level', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['account_id'], [f'{database_schema}.account.id'], ),
        sa.ForeignKeyConstraint(['default_unit_id'], [f'{database_schema}.unit.id'], ),
        schema=database_schema
    )

    op.create_table('inventory_item_units',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('inventory_item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('from_unit_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('to_unit_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversion_factor', sa.Numeric(precision=12, scale=6), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['inventory_item_id'], [f'{database_schema}.inventory_item.id'], ),
        sa.ForeignKeyConstraint(['from_unit_id'], [f'{database_schema}.unit.id'], ),
        sa.ForeignKeyConstraint(['to_unit_id'], [f'{database_schema}.unit.id'], ),
        schema=database_schema
    )

    op.create_table('inventory_stock',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('store_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('inventory_item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('unit_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('lot_number', sa.String(), nullable=True),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['store_id'], [f'{database_schema}.store.id'], ),
        sa.ForeignKeyConstraint(['inventory_item_id'], [f'{database_schema}.inventory_item.id'], ),
        sa.ForeignKeyConstraint(['unit_id'], [f'{database_schema}.unit.id'], ),
        schema=database_schema
    )

    # Supplier documents
    op.create_table('document',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('restaurant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('store_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('supplier_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('document_type', sa.String(), nullable=False),
        sa.Column('file_name', sa.String(), nullable=False),
        sa.Column('file_type', sa.String(), nullable=False),
        sa.Column('storage_path', sa.String(), nullable=False),
        sa.Column('upload_date', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(), nullable=False, default='uploaded'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('doc_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.ForeignKeyConstraint(['account_id'], [f'{database_schema}.account.id'], ),
        sa.ForeignKeyConstraint(['restaurant_id'], [f'{database_schema}.restaurant.id'], ),
        sa.ForeignKeyConstraint(['store_id'], [f'{database_schema}.store.id'], ),
        sa.ForeignKeyConstraint(['supplier_id'], [f'{database_schema}.supplier.id'], ),
        schema=database_schema
    )

    # Purchasing
    op.create_table('purchase_order',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('supplier_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('po_number', sa.String(), nullable=True),
        sa.Column('expected_delivery_date', sa.Date(), nullable=True),
        sa.Column('delivery_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['account_id'], [f'{database_schema}.account.id'], ),
        sa.ForeignKeyConstraint(['supplier_id'], [f'{database_schema}.supplier.id'], ),
        schema=database_schema
    )

    op.create_table('purchase_order_item',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('purchase_order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('inventory_item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('unit_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('received_quantity', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['purchase_order_id'], [f'{database_schema}.purchase_order.id'], ),
        sa.ForeignKeyConstraint(['inventory_item_id'], [f'{database_schema}.inventory_item.id'], ),
        sa.ForeignKeyConstraint(['unit_id'], [f'{database_schema}.unit.id'], ),
        schema=database_schema
    )

    # Staff onboarding
    op.create_table('staff_onboarding',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('restaurant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('position', sa.String(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, default='in_progress'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.ForeignKeyConstraint(['restaurant_id'], [f'{database_schema}.restaurant.id'], ),
        schema=database_schema
    )

    op.create_table('onboarding_step',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('staff_onboarding_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, default='pending'),
        sa.Column('completion_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.ForeignKeyConstraint(['staff_onboarding_id'], [f'{database_schema}.staff_onboarding.id'], ),
        schema=database_schema
    )

    # Recipes and Menu
    op.create_table('recipe',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('instructions', sa.Text(), nullable=True),
        sa.Column('yield_quantity', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('yield_unit_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('prep_time_minutes', sa.Integer(), nullable=True),
        sa.Column('cook_time_minutes', sa.Integer(), nullable=True),
        sa.Column('image_url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['account_id'], [f'{database_schema}.account.id'], ),
        sa.ForeignKeyConstraint(['yield_unit_id'], [f'{database_schema}.unit.id'], ),
        schema=database_schema
    )

    op.create_table('recipe_ingredient',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('recipe_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('inventory_item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('unit_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['recipe_id'], [f'{database_schema}.recipe.id'], ),
        sa.ForeignKeyConstraint(['inventory_item_id'], [f'{database_schema}.inventory_item.id'], ),
        sa.ForeignKeyConstraint(['unit_id'], [f'{database_schema}.unit.id'], ),
        schema=database_schema
    )

    op.create_table('recipe_step',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('recipe_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('step_number', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['recipe_id'], [f'{database_schema}.recipe.id'], ),
        schema=database_schema
    )

    op.create_table('menu_item',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('recipe_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('base_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('image_url', sa.String(), nullable=True),
        sa.Column('is_available', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['account_id'], [f'{database_schema}.account.id'], ),
        sa.ForeignKeyConstraint(['recipe_id'], [f'{database_schema}.recipe.id'], ),
        schema=database_schema
    )

    op.create_table('menu',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('restaurant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('start_time', sa.Time(), nullable=True),
        sa.Column('end_time', sa.Time(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.ForeignKeyConstraint(['restaurant_id'], [f'{database_schema}.restaurant.id'], ),
        schema=database_schema
    )

    op.create_table('menu_contains_menu_item',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('menu_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('menu_item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('display_order', sa.Integer(), nullable=True),
        sa.Column('price_override', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['menu_id'], [f'{database_schema}.menu.id'], ),
        sa.ForeignKeyConstraint(['menu_item_id'], [f'{database_schema}.menu_item.id'], ),
        schema=database_schema
    )

    # Orders

    op.create_table('order',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('store_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_count', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['store_id'], [f'{database_schema}.store.id'], ),
        schema=database_schema
    )

    op.create_table('order_item',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('menu_item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('status', sa.String(), nullable=True, default='pending'),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['order_id'], [f'{database_schema}.order.id'], ),
        sa.ForeignKeyConstraint(['menu_item_id'], [f'{database_schema}.menu_item.id'], ),
        schema=database_schema
    )

    # Sales data
    op.create_table('sales_data',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('restaurant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('store_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('menu_item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quantity_sold', sa.Integer(), nullable=False),
        sa.Column('revenue', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('cost', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['restaurant_id'], [f'{database_schema}.restaurant.id'], ),
        sa.ForeignKeyConstraint(['store_id'], [f'{database_schema}.store.id'], ),
        sa.ForeignKeyConstraint(['menu_item_id'], [f'{database_schema}.menu_item.id'], ),
        schema=database_schema
    )

    # Bot management tables
    op.create_table('bot_instance',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['account_id'], [f'{database_schema}.account.id'], ),
        schema=database_schema
    )
    
    op.create_table('bot_platform_credential',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('bot_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('platform', sa.String(), nullable=False),
        sa.Column('credentials', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['bot_id'], [f'{database_schema}.bot_instance.id'], ),
        sa.UniqueConstraint('bot_id', 'platform', name='uix_bot_platform'),
        schema=database_schema
    )
    
    op.create_table('bot_scenario',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('bot_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('scenario_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('version', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['bot_id'], [f'{database_schema}.bot_instance.id'], ),
        schema=database_schema
    )
    
    op.create_table('bot_dialog_state',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('bot_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('platform', sa.String(), nullable=False),
        sa.Column('platform_chat_id', sa.String(), nullable=False),
        sa.Column('current_step', sa.String(), nullable=False),
        sa.Column('collected_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('last_interaction_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['bot_id'], [f'{database_schema}.bot_instance.id'], ),
        sa.UniqueConstraint('bot_id', 'platform', 'platform_chat_id', name='uix_bot_platform_chat'),
        schema=database_schema
    )
    
    op.create_table('bot_dialog_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('dialog_state_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message_type', sa.String(), nullable=False),
        sa.Column('message_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['dialog_state_id'], [f'{database_schema}.bot_dialog_state.id'], ),
        schema=database_schema
    )
    
    op.create_table('bot_media_file',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('bot_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_type', sa.String(), nullable=False),
        sa.Column('file_name', sa.String(), nullable=False),
        sa.Column('storage_path', sa.String(), nullable=False),
        sa.Column('platform_file_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['bot_id'], [f'{database_schema}.bot_instance.id'], ),
        schema=database_schema
    )
    
    # Create indexes for better performance
    # Account indexes
    op.create_index('ix_account_name', 'account', ['name'], unique=False, schema=database_schema)
    
    # Restaurant indexes
    op.create_index('ix_restaurant_account_id', 'restaurant', ['account_id'], unique=False, schema=database_schema)
    op.create_index('ix_restaurant_name', 'restaurant', ['name'], unique=False, schema=database_schema)
    
    # Store indexes
    op.create_index('ix_store_restaurant_id', 'store', ['restaurant_id'], unique=False, schema=database_schema)
    
    # User indexes
    # Removed email index as email field was removed from user_profile
    op.create_index('ix_user_profile_account_id', 'user_profile', ['account_id'], unique=False, schema=database_schema)
    
    # Inventory indexes
    op.create_index('ix_inventory_item_account_id', 'inventory_item', ['account_id'], unique=False, schema=database_schema)
    op.create_index('ix_inventory_item_name', 'inventory_item', ['name'], unique=False, schema=database_schema)
    op.create_index('ix_inventory_stock_store_id', 'inventory_stock', ['store_id'], unique=False, schema=database_schema)
    op.create_index('ix_inventory_stock_inventory_item_id', 'inventory_stock', ['inventory_item_id'], unique=False, schema=database_schema)
    
    # Recipe and menu indexes
    op.create_index('ix_recipe_account_id', 'recipe', ['account_id'], unique=False, schema=database_schema)
    op.create_index('ix_menu_item_account_id', 'menu_item', ['account_id'], unique=False, schema=database_schema)
    op.create_index('ix_menu_restaurant_id', 'menu', ['restaurant_id'], unique=False, schema=database_schema)
    
    # Order indexes
    op.create_index('ix_order_store_id', 'order', ['store_id'], unique=False, schema=database_schema)
    op.create_index('ix_order_status', 'order', ['status'], unique=False, schema=database_schema)
    op.create_index('ix_order_created_at', 'order', ['created_at'], unique=False, schema=database_schema)
    
    # Bot indexes
    op.create_index('ix_bot_instance_account_id', 'bot_instance', ['account_id'], unique=False, schema=database_schema)
    op.create_index('ix_bot_platform_credential_bot_id', 'bot_platform_credential', ['bot_id'], unique=False, schema=database_schema)
    op.create_index('ix_bot_scenario_bot_id', 'bot_scenario', ['bot_id'], unique=False, schema=database_schema)
    op.create_index('ix_bot_dialog_state_bot_id', 'bot_dialog_state', ['bot_id'], unique=False, schema=database_schema)
    op.create_index('ix_bot_dialog_state_platform_chat_id', 'bot_dialog_state', ['platform_chat_id'], unique=False, schema=database_schema)


def downgrade():
    # Drop all tables in reverse order
    # Bot tables
    op.drop_table('bot_media_file', schema=database_schema)
    op.drop_table('bot_dialog_history', schema=database_schema)
    op.drop_table('bot_dialog_state', schema=database_schema)
    op.drop_table('bot_scenario', schema=database_schema)
    op.drop_table('bot_platform_credential', schema=database_schema)
    op.drop_table('bot_instance', schema=database_schema)
    
    # Other tables
    op.drop_table('sales_data', schema=database_schema)
    op.drop_table('order_item', schema=database_schema)
    op.drop_table('order', schema=database_schema)
    # Restaurant table was moved to a separate migration
    op.drop_table('menu_contains_menu_item', schema=database_schema)
    op.drop_table('menu', schema=database_schema)
    op.drop_table('menu_item', schema=database_schema)
    op.drop_table('recipe_step', schema=database_schema)
    op.drop_table('recipe_ingredient', schema=database_schema)
    op.drop_table('recipe', schema=database_schema)
    op.drop_table('onboarding_step', schema=database_schema)
    op.drop_table('staff_onboarding', schema=database_schema)
    op.drop_table('purchase_order_item', schema=database_schema)
    op.drop_table('purchase_order', schema=database_schema)
    op.drop_table('document', schema=database_schema)
    op.drop_table('inventory_stock', schema=database_schema)
    op.drop_table('inventory_item_units', schema=database_schema)
    op.drop_table('inventory_item', schema=database_schema)
    op.drop_table('unit_conversion', schema=database_schema)
    op.drop_table('unit', schema=database_schema)
    op.drop_table('unit_category', schema=database_schema)
    op.drop_table('user_profile', schema=database_schema)
    op.drop_table('supplier', schema=database_schema)
    op.drop_table('store', schema=database_schema)
    op.drop_table('restaurant', schema=database_schema)
    op.drop_table('account', schema=database_schema)
    
    # Drop schema
    op.execute(f'DROP SCHEMA IF EXISTS {database_schema} CASCADE')