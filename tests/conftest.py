"""
Shared pytest fixtures for auth tests.

Strategy: override the FastAPI `get_db` dependency with a mock session
so tests never touch a real database.
"""
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from main import app
from db.connection import get_db


def get_mock_db():
    """A no-op DB session mock."""
    return MagicMock()


@pytest.fixture
def mock_db():
    """Pytest fixture that yields a fresh MagicMock session."""
    return MagicMock()


@pytest.fixture
def client(mock_db):
    """
    TestClient fixture with the real `get_db` dependency replaced
    by a mock so no real DB connection is needed.
    """
    app.dependency_overrides[get_db] = lambda: mock_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
