import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Repo root isn't on sys.path when alembic runs from migrations/ -- needed to
# import `config`/`database` below.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import DATABASE_URL  # noqa: E402
from database import Base  # noqa: E402

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Real DB URL always comes from the app's own config (env vars), not the
# static alembic.ini placeholder -- so `alembic upgrade head` targets
# whatever DATABASE_URL the running environment actually has, dev or prod.
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Interpret the config file for Python logging. disable_existing_loggers=False
# is required here (default fileConfig() behavior is True) -- this runs
# inside the live app's process via database.run_migrations(), after
# logging_config.setup_logging() has already configured the app's own
# loggers; the default would silently disable all of them process-wide.
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
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
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
