import pytest
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.postgres import get_session
from app.main import app

# Set pytest-asyncio mode to auto
pytestmark = pytest.mark.asyncio
pytest_plugins = ["pytest_asyncio"]


# This fixture is used to create a test client for FastAPI
@pytest.fixture
def client() -> Generator:
    with TestClient(app) as c:
        yield c


# This fixture is used to create a test database session
@pytest.fixture
async def mock_db_session() -> AsyncGenerator:
    mock_session = AsyncMock(spec=AsyncSession)
    yield mock_session


# Override the get_db dependency to use our test session
@pytest.fixture
def override_get_db(mock_db_session: AsyncSession):
    async def _override_get_db():
        yield mock_db_session

    app.dependency_overrides[get_session] = _override_get_db
    yield
    app.dependency_overrides = {} 