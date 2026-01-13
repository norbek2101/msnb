import pytest
from uuid import uuid4


class TestLikePost:

    @pytest.mark.asyncio
    async def test_like_post_success(self, user_with_post, second_verified_user, async_client):
        post_id = user_with_post["post"]["id"]
        response = await async_client.post(
            f"/posts/{post_id}/like",
            headers=second_verified_user["headers"]
        )

        assert response.status_code == 201
        data = response.json()
        assert data["post_id"] == post_id
        assert data["user_id"] == second_verified_user["user"]["id"]

    @pytest.mark.asyncio
    async def test_like_own_post_forbidden(self, user_with_post, async_client):
        post_id = user_with_post["post"]["id"]
        response = await async_client.post(
            f"/posts/{post_id}/like",
            headers=user_with_post["headers"]
        )

        assert response.status_code == 400
        assert "Cannot like your own post" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_like_already_liked_post(self, user_with_post, second_verified_user, async_client):
        post_id = user_with_post["post"]["id"]
        
        await async_client.post(
            f"/posts/{post_id}/like",
            headers=second_verified_user["headers"]
        )
        
        response = await async_client.post(
            f"/posts/{post_id}/like",
            headers=second_verified_user["headers"]
        )

        assert response.status_code == 400
        assert "Already liked" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_like_nonexistent_post(self, verified_user, async_client):
        fake_id = str(uuid4())
        response = await async_client.post(
            f"/posts/{fake_id}/like",
            headers=verified_user["headers"]
        )

        assert response.status_code == 404
        assert "Post not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_like_unauthenticated(self, user_with_post, async_client):
        post_id = user_with_post["post"]["id"]
        response = await async_client.post(f"/posts/{post_id}/like")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_like_reflected_in_post_details(self, user_with_post, second_verified_user, async_client):
        post_id = user_with_post["post"]["id"]
        
        await async_client.post(
            f"/posts/{post_id}/like",
            headers=second_verified_user["headers"]
        )
        
        response = await async_client.get(f"/posts/{post_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["likes_count"] == 1
        assert second_verified_user["user"]["id"] in data["likes"]


class TestUnlikePost:

    @pytest.mark.asyncio
    async def test_unlike_post_success(self, user_with_post, second_verified_user, async_client):
        post_id = user_with_post["post"]["id"]
        
        await async_client.post(
            f"/posts/{post_id}/like",
            headers=second_verified_user["headers"]
        )
        
        response = await async_client.delete(
            f"/posts/{post_id}/like",
            headers=second_verified_user["headers"]
        )
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_unlike_post_not_liked(self, user_with_post, second_verified_user, async_client):
        post_id = user_with_post["post"]["id"]
        response = await async_client.delete(
            f"/posts/{post_id}/like",
            headers=second_verified_user["headers"]
        )

        assert response.status_code == 404
        assert "Like not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_unlike_nonexistent_post(self, verified_user, async_client):
        fake_id = str(uuid4())
        response = await async_client.delete(
            f"/posts/{fake_id}/like",
            headers=verified_user["headers"]
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_unlike_unauthenticated(self, user_with_post, async_client):
        post_id = user_with_post["post"]["id"]
        response = await async_client.delete(f"/posts/{post_id}/like")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_unlike_reflected_in_post_details(self, user_with_post, second_verified_user, async_client):
        post_id = user_with_post["post"]["id"]
        
        await async_client.post(
            f"/posts/{post_id}/like",
            headers=second_verified_user["headers"]
        )
        await async_client.delete(
            f"/posts/{post_id}/like",
            headers=second_verified_user["headers"]
        )
        
        response = await async_client.get(f"/posts/{post_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["likes_count"] == 0
        assert second_verified_user["user"]["id"] not in data["likes"]
