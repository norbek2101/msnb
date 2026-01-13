import pytest
from unittest.mock import patch


class TestGetProfile:

    @pytest.mark.asyncio
    async def test_get_profile_authenticated(self, async_client, test_user_data):
        with patch("app.services.auth_service.send_email_task"):
            await async_client.post("/auth/register", json=test_user_data)

        login_response = await async_client.post(
            "/auth/login",
            data={"username": test_user_data["email"], "password": test_user_data["password"]}
        )
        token = login_response.json()["access_token"]

        response = await async_client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["username"] == test_user_data["username"]
        assert data["full_name"] == test_user_data["full_name"]

    @pytest.mark.asyncio
    async def test_get_profile_unauthenticated(self, async_client):
        response = await async_client.get("/users/me")
        assert response.status_code == 401


class TestUpdateProfile:

    @pytest.mark.asyncio
    async def test_update_username_success(self, unverified_user, async_client):
        response = await async_client.patch(
            "/users/me",
            json={"username": "newusername"},
            headers=unverified_user["headers"]
        )

        assert response.status_code == 200
        assert response.json()["username"] == "newusername"

    @pytest.mark.asyncio
    async def test_update_username_already_taken(self, async_client, test_user_data, test_user_data_2):
        with patch("app.services.auth_service.send_email_task"):
            await async_client.post("/auth/register", json=test_user_data)
            await async_client.post("/auth/register", json=test_user_data_2)

        login_response = await async_client.post(
            "/auth/login",
            data={"username": test_user_data_2["email"], "password": test_user_data_2["password"]}
        )
        token = login_response.json()["access_token"]

        response = await async_client.patch(
            "/users/me",
            json={"username": test_user_data["username"]},
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 400
        assert "Username already taken" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_username_invalid_format(self, unverified_user, async_client):
        response = await async_client.patch(
            "/users/me",
            json={"username": "invalid@user"},
            headers=unverified_user["headers"]
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_username_too_short(self, unverified_user, async_client):
        response = await async_client.patch(
            "/users/me",
            json={"username": "ab"},
            headers=unverified_user["headers"]
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_full_name_success(self, unverified_user, async_client):
        response = await async_client.patch(
            "/users/me",
            json={"full_name": "New Full Name"},
            headers=unverified_user["headers"]
        )

        assert response.status_code == 200
        assert response.json()["full_name"] == "New Full Name"

    @pytest.mark.asyncio
    async def test_update_full_name_invalid(self, unverified_user, async_client):
        response = await async_client.patch(
            "/users/me",
            json={"full_name": "Invalid@Name#123"},
            headers=unverified_user["headers"]
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_both_fields(self, unverified_user, async_client):
        response = await async_client.patch(
            "/users/me",
            json={"username": "brandnew", "full_name": "Brand New Name"},
            headers=unverified_user["headers"]
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "brandnew"
        assert data["full_name"] == "Brand New Name"

    @pytest.mark.asyncio
    async def test_update_profile_unauthenticated(self, async_client):
        response = await async_client.patch(
            "/users/me",
            json={"full_name": "New Name"}
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_profile_empty_body(self, unverified_user, async_client):
        original_username = unverified_user["user"]["username"]
        response = await async_client.patch(
            "/users/me",
            json={},
            headers=unverified_user["headers"]
        )

        assert response.status_code == 200
        assert response.json()["username"] == original_username

    @pytest.mark.asyncio
    async def test_update_username_to_same_value(self, unverified_user, async_client):
        response = await async_client.patch(
            "/users/me",
            json={"username": unverified_user["user"]["username"]},
            headers=unverified_user["headers"]
        )
        assert response.status_code == 200
