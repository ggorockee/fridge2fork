from logging.config import fileConfig
import os
from dotenv import load_dotenv

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Load environment variables
load_dotenv()

# DATABASE_URL이 없으면 POSTGRES_* 환경변수로 구성
def get_database_url():
    """환경변수에서 DATABASE_URL 가져오기 또는 구성"""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    # DATABASE_URL이 없으면 개별 환경변수로 구성
    db = os.getenv("POSTGRES_DB")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST") or os.getenv("POSTGRES_SERVER")
    port = os.getenv("POSTGRES_PORT", "5432")

    if all([db, user, password, host]):
        database_url = f"postgresql://{user}:{password}@{host}:{port}/{db}"
        # 환경변수에 설정해서 다른 곳에서도 사용 가능하게
        os.environ["DATABASE_URL"] = database_url
        print(f"🔗 DATABASE_URL 자동 구성: postgresql://{user}:***@{host}:{port}/{db}")
        return database_url

    return None

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
from app.db.base import Base
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
    url = get_database_url()
    if url is None:
        raise ValueError("DATABASE_URL could not be determined from environment variables")

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
    # Get DATABASE_URL from environment
    database_url = get_database_url()
    if database_url is None:
        raise ValueError("DATABASE_URL could not be determined from environment variables")

    # Create configuration with database URL
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = database_url

    connectable = engine_from_config(
        configuration,
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
