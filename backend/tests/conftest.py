import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from mongomock_motor import AsyncMongoMockClient
from app.main import app
import app.database as db_module


@pytest_asyncio.fixture(loop_scope="session", autouse=True)
async def db_setup():
    client = AsyncMongoMockClient()
    db_module.set_database(client[db_module.settings.MONGODB_DATABASE])
    await db_module.create_indexes()
    yield
    client.close()


@pytest_asyncio.fixture
async def client(db_setup):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
