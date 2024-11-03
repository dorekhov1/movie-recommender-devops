import asyncio
import os
import time

import pytest
from httpx import ASGITransport, AsyncClient

from fallback_solution.app import app as fallback_app
from proper_solution.app import app

API_BASE_URL = os.getenv("API_BASE_URL", "")


@pytest.fixture(params=["proper", "fallback"])
def async_client(client_type):
    app_instance = app if client_type.param == "proper" else fallback_app
    transport = ASGITransport(app=app_instance)
    return AsyncClient(transport=transport, base_url=API_BASE_URL)


class TestAsyncAPI:
    @pytest.mark.asyncio
    async def test_health_check(self, async_client):
        response = await async_client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    @pytest.mark.asyncio
    async def test_recommendations_endpoint(self, async_client):
        response = await async_client.post(
            "/recommend", json={"user_id": 1, "n_recommendations": 5}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["recommendations"]) == 5

    @pytest.mark.asyncio
    @pytest.mark.parametrize("user_id", [1, 2, 3, 4, 5])
    async def test_multiple_users(self, async_client, user_id):
        response = await async_client.post(
            "/recommend", json={"user_id": user_id, "n_recommendations": 5}
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_service_latency(self, async_client):
        start_time = time.time()
        await async_client.post("/recommend", json={"user_id": 1, "n_recommendations": 5})
        end_time = time.time()
        assert (end_time - start_time) < 1.0

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, async_client):
        user_ids = range(1, 11)

        async def get_recommendations(user_id):
            return await async_client.post(
                "/recommend", json={"user_id": user_id, "n_recommendations": 5}
            )

        responses = await asyncio.gather(*[get_recommendations(user_id) for user_id in user_ids])
        assert all(response.status_code == 200 for response in responses)

    @pytest.mark.asyncio
    async def test_concurrent_mixed_requests(self, async_client):
        async def get_health():
            return await async_client.get("/health")

        async def get_recommendations(user_id):
            return await async_client.post(
                "/recommend", json={"user_id": user_id, "n_recommendations": 5}
            )

        requests = [
            get_health(),
            get_recommendations(1),
            get_health(),
            get_recommendations(2),
            get_recommendations(3),
        ]

        responses = await asyncio.gather(*requests)
        assert all(response.status_code == 200 for response in responses)
