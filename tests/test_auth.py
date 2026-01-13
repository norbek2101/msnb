import pytest
from unittest.mock import patch
from datetime import datetime, timedelta


class TestRegistration:

    @pytest.mark.asyncio
    async def test_register_success(self, async_client, test_user_data):
        with patch("app.services.auth_service.send_email_task"):
            response = await async_client.post("/auth/register", json=test_user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["username"] == test_user_data["username"]
        assert data["full_name"] == test_user_data["full_name"]
        assert data["is_verified"] == False
        assert "id" in data
        assert "password" not in data
        assert "password_hash" not in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, async_client, test_user_data):
        with patch("app.services.auth_service.send_email_task"):
            await async_client.post("/auth/register", json=test_user_data)
            response = await async_client.post("/auth/register", json=test_user_data)

        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, async_client, test_user_data, test_user_data_2):
        with patch("app.services.auth_service.send_email_task"):
            await async_client.post("/auth/register", json=test_user_data)
            test_user_data_2["username"] = test_user_data["username"]
            response = await async_client.post("/auth/register", json=test_user_data_2)

        assert response.status_code == 400
        assert "Username already taken" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_username_too_short(self, async_client, test_user_data):
        test_user_data["username"] = "ab"
        response = await async_client.post("/auth/register", json=test_user_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_username_too_long(self, async_client, test_user_data):
        test_user_data["username"] = "a" * 33
        response = await async_client.post("/auth/register", json=test_user_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_username_special_chars(self, async_client, test_user_data):
        test_user_data["username"] = "user@name"
        response = await async_client.post("/auth/register", json=test_user_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, async_client, test_user_data):
        test_user_data["email"] = "not-an-email"
        response = await async_client.post("/auth/register", json=test_user_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_password_too_short(self, async_client, test_user_data):
        test_user_data["password"] = "12345"
        response = await async_client.post("/auth/register", json=test_user_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_full_name_too_short(self, async_client, test_user_data):
        test_user_data["full_name"] = "A"
        response = await async_client.post("/auth/register", json=test_user_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_full_name_special_chars(self, async_client, test_user_data):
        test_user_data["full_name"] = "Test@User#123"
        response = await async_client.post("/auth/register", json=test_user_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_missing_email(self, async_client, test_user_data):
        del test_user_data["email"]
        response = await async_client.post("/auth/register", json=test_user_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_missing_password(self, async_client, test_user_data):
        del test_user_data["password"]
        response = await async_client.post("/auth/register", json=test_user_data)
        assert response.status_code == 422


class TestLogin:

    @pytest.mark.asyncio
    async def test_login_with_email_success(self, async_client, test_user_data):
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
    async def test_login_with_username_success(self, async_client, test_user_data):
        with patch("app.services.auth_service.send_email_task"):
            await async_client.post("/auth/register", json=test_user_data)

        response = await async_client.post(
            "/auth/login",
            data={"username": test_user_data["username"], "password": test_user_data["password"]}
        )

        assert response.status_code == 200
        assert "access_token" in response.json()

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, async_client, test_user_data):
        with patch("app.services.auth_service.send_email_task"):
            await async_client.post("/auth/register", json=test_user_data)

        response = await async_client.post(
            "/auth/login",
            data={"username": test_user_data["email"], "password": "wrongpassword"}
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, async_client):
        response = await async_client.post(
            "/auth/login",
            data={"username": "nonexistent@example.com", "password": "password123"}
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_empty_credentials(self, async_client):
        response = await async_client.post(
            "/auth/login",
            data={"username": "", "password": ""}
        )
        assert response.status_code in [401, 422]


class TestGetMe:

    @pytest.mark.asyncio
    async def test_get_me_with_valid_token(self, async_client, test_user_data):
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
        assert data["username"] == test_user_data["username"]

    @pytest.mark.asyncio
    async def test_get_me_without_token(self, async_client):
        response = await async_client.get("/auth/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_me_invalid_token(self, async_client):
        response = await async_client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalidtoken"}
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_me_malformed_header(self, async_client):
        response = await async_client.get(
            "/auth/me",
            headers={"Authorization": "NotBearer token"}
        )
        assert response.status_code == 401


class TestEmailVerification:

    @pytest.mark.asyncio
    async def test_verify_email_success(self, async_client, test_user_data, db_session):
        with patch("app.services.auth_service.send_email_task"):
            await async_client.post("/auth/register", json=test_user_data)

        from sqlalchemy import select
        from app.models import EmailVerificationToken, User
        
        result = await db_session.execute(
            select(EmailVerificationToken).join(User).where(User.email == test_user_data["email"])
        )
        token_record = result.scalars().first()

        response = await async_client.get(f"/auth/verify-email?token={token_record.token}")

        assert response.status_code == 200
        assert "Email verified successfully" in response.json()["message"]

        user_result = await db_session.execute(
            select(User).where(User.email == test_user_data["email"])
        )
        user = user_result.scalars().first()
        await db_session.refresh(user)
        assert user.is_verified == True

    @pytest.mark.asyncio
    async def test_verify_email_invalid_token(self, async_client):
        response = await async_client.get("/auth/verify-email?token=invalid-token-12345")
        assert response.status_code == 400
        assert "Invalid verification token" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_verify_email_expired_token(self, async_client, test_user_data, db_session):
        with patch("app.services.auth_service.send_email_task"):
            await async_client.post("/auth/register", json=test_user_data)

        from sqlalchemy import select, update
        from app.models import EmailVerificationToken, User
        from datetime import datetime, timedelta
        
        await db_session.execute(
            update(EmailVerificationToken).values(expires_at=datetime.utcnow() - timedelta(hours=1))
        )
        await db_session.commit()

        result = await db_session.execute(
            select(EmailVerificationToken).join(User).where(User.email == test_user_data["email"])
        )
        token_record = result.scalars().first()

        response = await async_client.get(f"/auth/verify-email?token={token_record.token}")

        assert response.status_code == 400
        assert "expired" in response.json()["detail"].lower()


class TestResendVerification:

    @pytest.mark.asyncio
    async def test_resend_verification_success(self, unverified_user, async_client):
        with patch("app.services.auth_service.send_email_task"):
            response = await async_client.post(
                "/auth/resend-verification",
                headers=unverified_user["headers"]
            )

        assert response.status_code == 200
        assert "Verification email sent" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_resend_verification_already_verified(self, verified_user, async_client):
        with patch("app.services.auth_service.send_email_task"):
            response = await async_client.post(
                "/auth/resend-verification",
                headers=verified_user["headers"]
            )

        assert response.status_code == 400
        assert "already verified" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_resend_verification_unauthenticated(self, async_client):
        response = await async_client.post("/auth/resend-verification")
        assert response.status_code == 401
