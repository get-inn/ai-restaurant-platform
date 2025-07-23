# Database Migration Guide

This guide explains how to work with database migrations in the GET INN Restaurant Platform.

## Overview

The platform uses Alembic for database schema migrations. Migrations allow for controlled, versioned changes to the database schema that can be applied or rolled back as needed.

## Key Concepts

- **Revision**: A single migration script that applies a set of changes to the database
- **Head**: The latest migration revision
- **Upgrade**: Apply migrations forward to a newer version
- **Downgrade**: Revert migrations to an earlier version
- **Auto-generation**: Automatically generate migration scripts based on model changes

## Migration Directory Structure

```
/backend/migrations/
├── env.py               # Alembic environment configuration
├── README.md            # Information about migrations
├── script.py.mako       # Template for migration scripts
└── versions/            # Directory containing migration files
    ├── 01_initial.py    # First migration
    ├── 02_add_users.py  # Second migration
    └── ...              # Additional migrations
```

## Working with Migrations

### Creating a New Migration

#### Option 1: Auto-generate from model changes

This method compares your SQLAlchemy models with the current database schema and generates the appropriate migration script:

```bash
# Using Docker
./backend/start-dev.sh --exec backend alembic revision --autogenerate -m "description of changes"

# Using local virtual environment
cd backend
python -m alembic revision --autogenerate -m "description of changes"
```

#### Option 2: Create an empty migration

Use this method when you need more control over the migration:

```bash
# Using Docker
./backend/start-dev.sh --exec backend alembic revision -m "description of changes"

# Using local virtual environment
cd backend
python -m alembic revision -m "description of changes"
```

### Editing Migration Scripts

After generating a migration, review and edit it if necessary:

```python
# migrations/versions/123456789abc_description_of_changes.py

def upgrade():
    # Operations to perform when upgrading
    op.create_table(
        'my_new_table',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    # Operations to perform when downgrading
    op.drop_table('my_new_table')
```

### Applying Migrations

Apply pending migrations to bring the database schema up to date:

```bash
# Using Docker
./backend/start-dev.sh --exec backend alembic upgrade head

# Using local virtual environment
cd backend
python -m alembic upgrade head
```

### Reverting Migrations

Revert to a previous migration:

```bash
# Revert the most recent migration
./backend/start-dev.sh --exec backend alembic downgrade -1

# Revert to a specific migration by identifier
./backend/start-dev.sh --exec backend alembic downgrade 123456789abc

# Revert all migrations
./backend/start-dev.sh --exec backend alembic downgrade base
```

### Check Migration Status

Check the current migration status:

```bash
# Using Docker
./backend/start-dev.sh --exec backend alembic current

# List migration history
./backend/start-dev.sh --exec backend alembic history
```

## Database Schema

The platform uses a dedicated PostgreSQL schema named `getinn_ops` instead of the default `public` schema. This helps isolate our application's tables from other applications using the same database.

### Schema Configuration

In `env.py` and models, the schema is set from environment variables:

```python
# In env.py
schema = os.environ.get("DATABASE_SCHEMA", "getinn_ops")
target_metadata = sa.MetaData(schema=schema)
```

Make sure your models also use the schema:

```python
# In model definitions
__table_args__ = {"schema": settings.DATABASE_SCHEMA}
```

### Environment Variables

Set the database schema in your environment:

```bash
# In .env file or Docker configuration
DATABASE_SCHEMA=getinn_ops
```

## Common Migration Operations

### Adding a Table

```python
def upgrade():
    op.create_table(
        'new_table',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema=settings.DATABASE_SCHEMA
    )
```

### Adding a Column

```python
def upgrade():
    op.add_column('existing_table', 
                  sa.Column('new_column', sa.String(255), nullable=True),
                  schema=settings.DATABASE_SCHEMA)
```

### Modifying a Column

```python
def upgrade():
    op.alter_column('existing_table', 'existing_column',
                    existing_type=sa.String(50),
                    type_=sa.String(100),
                    nullable=False,
                    schema=settings.DATABASE_SCHEMA)
```

### Adding Constraints

```python
def upgrade():
    # Add a foreign key
    op.create_foreign_key(
        'fk_order_user',
        'order', 'user',
        ['user_id'], ['id'],
        source_schema=settings.DATABASE_SCHEMA,
        referent_schema=settings.DATABASE_SCHEMA
    )
    
    # Add a unique constraint
    op.create_unique_constraint(
        'uq_email_account',
        'user',
        ['email', 'account_id'],
        schema=settings.DATABASE_SCHEMA
    )
```

### Adding an Index

```python
def upgrade():
    op.create_index(
        'ix_user_email',
        'user',
        ['email'],
        unique=True,
        schema=settings.DATABASE_SCHEMA
    )
```

## Best Practices

1. **Always review auto-generated migrations** before applying them, especially in production environments.

2. **Include both upgrade and downgrade operations** to ensure migrations can be rolled back if needed.

3. **Test migrations thoroughly** before deploying to production:
   ```bash
   # Apply and then roll back to test both paths
   ./backend/start-dev.sh --exec backend alembic upgrade head
   ./backend/start-dev.sh --exec backend alembic downgrade -1
   ./backend/start-dev.sh --exec backend alembic upgrade head
   ```

4. **Use meaningful migration names** that clearly describe the changes.

5. **Keep migrations small and focused** on specific changes to minimize risk.

6. **Don't modify existing migrations** that have been applied to any environment. Instead, create a new migration to make additional changes.

7. **Include data migrations when necessary**, such as when new columns need to be populated with values:
   ```python
   def upgrade():
       # Add column
       op.add_column('user', sa.Column('full_name', sa.String(255), nullable=True))
       
       # Data migration
       op.execute("""
           UPDATE getinn_ops.user 
           SET full_name = first_name || ' ' || last_name 
           WHERE first_name IS NOT NULL AND last_name IS NOT NULL
       """)
   ```

## Troubleshooting

### Common Issues

1. **"Table already exists" errors**:
   - Make sure your migration isn't trying to create a table that already exists.
   - Check if auto-generation is picking up tables that exist but aren't in your SQLAlchemy models.

2. **Changes not reflected in database**:
   - Verify that you've run `alembic upgrade head` after creating your migration.
   - Check that the migration file was created in the correct location.

3. **"Target database is not up to date" error**:
   - Run `alembic heads` to see the current heads.
   - Run `alembic current` to see the current revision.
   - You may need to manually edit the alembic_version table if there are inconsistencies.

### Fixing a Failed Migration

If a migration fails partway through:

1. Fix the issue in the migration script.
2. Try running the upgrade again:
   ```bash
   ./backend/start-dev.sh --exec backend alembic upgrade head
   ```

3. If it still fails, you may need to manually fix the database state or roll back:
   ```bash
   # Roll back to the previous working migration
   ./backend/start-dev.sh --exec backend alembic downgrade <previous_revision>
   ```

## Advanced Usage

### Multiple Branch Migrations

If you have multiple developers working on migrations simultaneously, you might end up with multiple heads:

```bash
# Check if you have multiple heads
./backend/start-dev.sh --exec backend alembic heads

# Merge multiple heads
./backend/start-dev.sh --exec backend alembic merge -m "merge branches" <revision1> <revision2>
```

### Stamping the Current Database Version

If you need to mark the database as being at a specific revision without applying changes:

```bash
./backend/start-dev.sh --exec backend alembic stamp <revision>
```