import pytest
from app.database.connection import init_db
from app.database import models  # noqa: F401

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    init_db()
    yield
