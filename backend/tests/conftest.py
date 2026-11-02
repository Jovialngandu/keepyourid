
import pytest

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="session")
def test_engine():
    database_url = (
        "postgresql+psycopg://keepyourid:keepyourid_dev"
        "@localhost:5434/keepyourid_test_db"
    )

    engine = create_engine(database_url, pool_pre_ping=True)

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    command.upgrade(alembic_cfg, "head")

    yield engine

    engine.dispose()


@pytest.fixture
def db_session(test_engine):
    connection = test_engine.connect()
    outer_transaction = connection.begin()

    TestingSessionLocal = sessionmaker(
        bind=connection,
        autoflush=False,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )

    session = TestingSessionLocal()
    session.begin_nested()

    try:
        yield session
    finally:
        session.rollback()
        session.close()
        outer_transaction.rollback()
        connection.close()
