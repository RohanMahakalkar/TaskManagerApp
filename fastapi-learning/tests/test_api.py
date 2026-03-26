import os
import pytest
from httpx import AsyncClient, ASGITransport

os.environ["MONGO_DB"] = "taskdb_test"

from main import app
from database import users_collection, tasks_collection
from cache import redis_client


@pytest.fixture(autouse=True)
def clear_db():
    users_collection.delete_many({})
    tasks_collection.delete_many({})
    yield
    users_collection.delete_many({})
    tasks_collection.delete_many({})


@pytest.mark.asyncio
async def test_full_task_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # signup
        r = await client.post("/signup", json={"username": "alice", "password": "sekret"})
        assert r.status_code == 200

        # login
        r = await client.post("/login", data={"username": "alice", "password": "sekret"})
        assert r.status_code == 200
        token = r.json()["access_token"]

        # create task
        r = await client.post(
            "/tasks",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "My first task"},
        )
        assert r.status_code == 200
        task_id = r.json()["task_id"]

        # list tasks with pagination & search
        r = await client.get(
            "/tasks?page=1&limit=5&search=first",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 1
        assert body["items"][0]["name"] == "My first task"

        # update task
        r = await client.put(
            f"/tasks/{task_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "My first task updated"},
        )
        assert r.status_code == 200

        # list tasks after update
        r = await client.get("/tasks", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["items"][0]["name"] == "My first task updated"

        # refresh token use
        refresh_token = (await client.post("/login", data={"username": "alice", "password": "sekret"})).json()["refresh_token"]
        r = await client.post("/token/refresh", json={"refresh_token": refresh_token})
        assert r.status_code == 200
        assert "access_token" in r.json()

        # delete task
        r = await client.delete(
            f"/tasks/{task_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200

        # verify deletion
        r = await client.get("/tasks", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["total"] == 0


@pytest.mark.asyncio
async def test_get_tasks_uses_redis_cache():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/signup", json={"username": "bob", "password": "sekret"})
        assert r.status_code == 200

        r = await client.post("/login", data={"username": "bob", "password": "sekret"})
        assert r.status_code == 200
        token = r.json()["access_token"]

        r = await client.post(
            "/tasks",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Cache me"},
        )
        assert r.status_code == 200

        r1 = await client.get("/tasks", headers={"Authorization": f"Bearer {token}"})
        assert r1.status_code == 200

        r2 = await client.get("/tasks", headers={"Authorization": f"Bearer {token}"})
        assert r2.status_code == 200
        assert r2.json()["total"] == 1

        if redis_client:
            keys = redis_client.keys("tasks:*")
            assert len(keys) >= 1
