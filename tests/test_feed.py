import pytest
from unittest.mock import patch


class TestGetFeed:

    @pytest.mark.asyncio
    async def test_get_feed_empty(self, async_client):
        response = await async_client.get("/all")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_get_feed_with_user(self, unverified_user, async_client):
        response = await async_client.get("/all")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_get_feed_pagination_params(self, async_client):
        response = await async_client.get("/all?page=1&page_size=5")
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5

    @pytest.mark.asyncio
    async def test_get_feed_invalid_page(self, async_client):
        response = await async_client.get("/all?page=0")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_feed_page_size_limit(self, async_client):
        response = await async_client.get("/all?page_size=200")
        assert response.status_code == 422
