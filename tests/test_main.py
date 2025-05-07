import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import engine, Base, AsyncSessionLocal
from app.models.user import User
from app.models.task import Task

client = TestClient(app)

@pytest.fixture
async def db_session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        yield session

@pytest.mark.asyncio
async def test_register(db_session):
    response = client.post("/register", json={"name": "Test", "email": "test@example.com", "password": "password"})
    assert response.status_code == 200
    assert response.json()["msg"] == "User registered"

@pytest.mark.asyncio
async def test_login(db_session):
    client.post("/register", json={"name": "Test", "email": "test@example.com", "password": "password"})
    response = client.post("/login", data={"username": "test@example.com", "password": "password"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()

@pytest.mark.asyncio
async def test_create_task(db_session):
    client.post("/register", json={"name": "Test", "email": "test@example.com", "password": "password"})
    login_response = client.post("/login", data={"username": "test@example.com", "password": "password"})
    token = login_response.json()["access_token"]
    response = client.post("/tasks", json={"title": "Test Task", "priority": 1}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["title"] == "Test Task"

@pytest.mark.asyncio
async def test_get_tasks(db_session):
    client.post("/register", json={"name": "Test", "email": "test@example.com", "password": "password"})
    login_response = client.post("/login", data={"username": "test@example.com", "password": "password"})
    token = login_response.json()["access_token"]
    client.post("/tasks", json={"title": "Test Task", "priority": 1}, headers={"Authorization": f"Bearer {token}"})
    response = client.get("/tasks", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert len(response.json()) == 1