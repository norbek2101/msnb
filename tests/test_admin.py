import pytest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone


class TestCleanupUnverifiedUsers:

    @pytest.mark.asyncio
    async def test_cleanup_no_users_to_delete(self, async_client):
        response = await async_client.post("/admin/cleanup-unverified")

        assert response.status_code == 200
        assert "Deleted 0 unverified users" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_cleanup_preserves_verified_users(self, verified_user, async_client, db_session):
        from sqlalchemy import update
        from app.models import User
        
        old_time = datetime.now(timezone.utc) - timedelta(hours=100)
        await db_session.execute(
            update(User).where(User.email == verified_user["data"]["email"]).values(created_at=old_time)
        )
        await db_session.commit()

        response = await async_client.post("/admin/cleanup-unverified")

        assert response.status_code == 200
        assert "Deleted 0 unverified users" in response.json()["message"]

        me_response = await async_client.get(
            "/auth/me",
            headers=verified_user["headers"]
        )
        assert me_response.status_code == 200

    @pytest.mark.asyncio
    async def test_cleanup_preserves_recent_unverified(self, unverified_user, async_client):
        response = await async_client.post("/admin/cleanup-unverified")

        assert response.status_code == 200
        assert "Deleted 0 unverified users" in response.json()["message"]

        me_response = await async_client.get(
            "/auth/me",
            headers=unverified_user["headers"]
        )
        assert me_response.status_code == 200

    @pytest.mark.asyncio
    async def test_cleanup_deletes_old_unverified(self, old_unverified_user, async_client):
        response = await async_client.post("/admin/cleanup-unverified")

        assert response.status_code == 200
        assert "Deleted 1 unverified users" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_cleanup_with_custom_hours(self, async_client, db_session):
        user_data = {
            "email": "custom_hours@example.com",
            "username": "customhours",
            "full_name": "Custom Hours User",
            "password": "password123"
        }
        with patch("app.services.auth_service.send_email_task"):
            await async_client.post("/auth/register", json=user_data)

        from sqlalchemy import update
        from app.models import User
        
        old_time = datetime.now(timezone.utc) - timedelta(hours=10)
        await db_session.execute(
            update(User).where(User.email == user_data["email"]).values(created_at=old_time)
        )
        await db_session.commit()

        response = await async_client.post("/admin/cleanup-unverified?hours=5")

        assert response.status_code == 200
        assert "older than 5 hours" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_cleanup_with_large_hours_threshold(self, async_client, db_session):
        user_data = {
            "email": "large_threshold@example.com",
            "username": "largethreshold",
            "full_name": "Large Threshold User",
            "password": "password123"
        }
        with patch("app.services.auth_service.send_email_task"):
            await async_client.post("/auth/register", json=user_data)

        from sqlalchemy import update
        from app.models import User
        
        old_time = datetime.now(timezone.utc) - timedelta(hours=10)
        await db_session.execute(
            update(User).where(User.email == user_data["email"]).values(created_at=old_time)
        )
        await db_session.commit()

        response = await async_client.post("/admin/cleanup-unverified?hours=100")

        assert response.status_code == 200
        assert "Deleted 0 unverified users" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_cleanup_multiple_users(self, async_client, db_session):
        from sqlalchemy import update
        from app.models import User
        
        for i in range(3):
            user_data = {
                "email": f"old_user_{i}@example.com",
                "username": f"olduser{i}",
                "full_name": f"Old User {i}",
                "password": "password123"
            }
            with patch("app.services.auth_service.send_email_task"):
                await async_client.post("/auth/register", json=user_data)

            old_time = datetime.now(timezone.utc) - timedelta(hours=100)
            await db_session.execute(
                update(User).where(User.email == user_data["email"]).values(created_at=old_time)
            )
        
        await db_session.commit()

        response = await async_client.post("/admin/cleanup-unverified")

        assert response.status_code == 200
        assert "Deleted 3 unverified users" in response.json()["message"]
