import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from keepyourid.core.database import Base
from keepyourid.modules.organizations.models import Organization


@pytest.fixture
def db_session():
    engine = create_engine(
        "postgresql+psycopg://keepyourid:keepyourid_dev@localhost:5434/keepyourid_db"
    )

    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()

        with engine.begin() as connection:
            connection.execute(
                Organization.__table__.delete()
            )

        engine.dispose()