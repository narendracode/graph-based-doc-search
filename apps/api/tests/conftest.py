import pytest
from sqlalchemy.orm import Session, sessionmaker

from api.db import engine


@pytest.fixture()
def db() -> Session:
    """A session bound to a transaction that's rolled back after the test, so
    tests never leave data behind in the (real, shared) Postgres instance."""
    connection = engine.connect()
    transaction = connection.begin()
    TestSession = sessionmaker(bind=connection)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
