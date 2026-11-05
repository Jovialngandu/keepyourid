
from uuid import uuid4

import pytest

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from keepyourid.core.auth import get_db
from keepyourid.main import app
from keepyourid.modules.users.models import User, UserStatus
from keepyourid.modules.users.service import UserService
from fastapi.testclient import TestClient


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


@pytest.fixture
def user(db_session):
    user = User(
        email=f"{uuid4().hex[:8]}@example.com",
        full_name="Test User",
        password_hash="test-password-hash",
        status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def authenticated_client(db_session, user):
    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = lambda: db_session

    _, token = UserService(db_session).create_session(user)

    try:
        with TestClient(app) as client:
            client.headers.update({
                "Authorization": f"Bearer {token}"
            })
            yield client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)