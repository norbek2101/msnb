import pytest
from unittest.mock import patch


@pytest.mark.asyncio
async def test_register_success(async_client, test_user_data):
    with patch("app.services.auth_service.send_email_task"):
        response = await async_client.post("/auth/register", json=test_user_data)

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert data["username"] == test_user_data["username"]
    assert data["full_name"] == test_user_data["full_name"]
    assert data["is_verified"] == False
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(async_client, test_user_data):
    with patch("app.services.auth_service.send_email_task"):
        await async_client.post("/auth/register", json=test_user_data)
        response = await async_client.post("/auth/register", json=test_user_data)

    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_duplicate_username(async_client, test_user_data, test_user_data_2):
    with patch("app.services.auth_service.send_email_task"):
        await async_client.post("/auth/register", json=test_user_data)
        test_user_data_2["username"] = test_user_data["username"]
        response = await async_client.post("/auth/register", json=test_user_data_2)

    assert response.status_code == 400
    assert "Username already taken" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_invalid_username_too_short(async_client, test_user_data):
    test_user_data["username"] = "ab"
    response = await async_client.post("/auth/register", json=test_user_data)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_username_special_chars(async_client, test_user_data):
    test_user_data["username"] = "user@name"
    response = await async_client.post("/auth/register", json=test_user_data)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_email(async_client, test_user_data):
    test_user_data["email"] = "not-an-email"
    response = await async_client.post("/auth/register", json=test_user_data)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(async_client, test_user_data):
    with patch("app.services.auth_service.send_email_task"):
        await async_client.post("/auth/register", json=test_user_data)

    response = await async_client.post(
        "/auth/login",
        data={"username": test_user_data["email"], "password": test_user_data["password"]}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_with_username(async_client, test_user_data):
    with patch("app.services.auth_service.send_email_task"):
        await async_client.post("/auth/register", json=test_user_data)

    response = await async_client.post(
        "/auth/login",
        data={"username": test_user_data["username"], "password": test_user_data["password"]}
    )

    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_wrong_password(async_client, test_user_data):
    with patch("app.services.auth_service.send_email_task"):
        await async_client.post("/auth/register", json=test_user_data)

    response = await async_client.post(
        "/auth/login",
        data={"username": test_user_data["email"], "password": "wrongpassword"}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(async_client):
    response = await async_client.post(
        "/auth/login",
        data={"username": "nonexistent@example.com", "password": "password123"}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_with_token(async_client, test_user_data):
    with patch("app.services.auth_service.send_email_task"):
        await async_client.post("/auth/register", json=test_user_data)

    login_response = await async_client.post(
        "/auth/login",
        data={"username": test_user_data["email"], "password": test_user_data["password"]}
    )
    token = login_response.json()["access_token"]

    response = await async_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user_data["email"]


@pytest.mark.asyncio
async def test_get_me_without_token(async_client):
    response = await async_client.get("/auth/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_invalid_token(async_client):
    response = await async_client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalidtoken"}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_profile(async_client, test_user_data):
    with patch("app.services.auth_service.send_email_task"):
        await async_client.post("/auth/register", json=test_user_data)

    login_response = await async_client.post(
        "/auth/login",
        data={"username": test_user_data["email"], "password": test_user_data["password"]}
    )
    token = login_response.json()["access_token"]

    response = await async_client.patch(
        "/users/me",
        json={"full_name": "Updated Name"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"
