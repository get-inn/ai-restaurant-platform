from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool, text
from sqlalchemy_utils import database_exists, create_database
from alembic import context
import os
import sys
from dotenv import load_dotenv

# Add the parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
load_dotenv()

# Import models
from src.api.models.base import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Get schema name
database_schema = os.getenv("DATABASE_SCHEMA", "getinn_ops")

# Override the SQLAlchemy URL with the one from environment
db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:5432/restaurant")
config.set_main_option("sqlalchemy.url", db_url)

# Create database if it doesn't exist
engine = engine_from_config(
    config.get_section(config.config_ini_section),
    prefix="sqlalchemy.",
    poolclass=pool.NullPool,
)

# Create database if it doesn't exist
if not database_exists(engine.url):
    create_database(engine.url)
    
# Create extension and schema
try:
    with engine.connect() as connection:
        connection = connection.execution_options(isolation_level="AUTOCOMMIT")
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""))
        connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {database_schema}"))
except Exception as e:
    print(f"Warning: Error during initialization: {e}")

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        version_table_schema=database_schema,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            include_schemas=True,
            version_table_schema=database_schema
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()