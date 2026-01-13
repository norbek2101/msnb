import pytest
from uuid import uuid4


class TestCreateComment:

    @pytest.mark.asyncio
    async def test_create_comment_success(self, user_with_post, second_verified_user, async_client, test_comment_data):
        post_id = user_with_post["post"]["id"]
        response = await async_client.post(
            f"/posts/{post_id}/comments",
            json=test_comment_data,
            headers=second_verified_user["headers"]
        )

        assert response.status_code == 201
        data = response.json()
        assert data["content"] == test_comment_data["content"]
        assert data["post_id"] == post_id
        assert data["author_id"] == second_verified_user["user"]["id"]

    @pytest.mark.asyncio
    async def test_create_comment_own_post(self, user_with_post, async_client, test_comment_data):
        post_id = user_with_post["post"]["id"]
        response = await async_client.post(
            f"/posts/{post_id}/comments",
            json=test_comment_data,
            headers=user_with_post["headers"]
        )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_create_comment_empty_content(self, user_with_post, second_verified_user, async_client):
        post_id = user_with_post["post"]["id"]
        response = await async_client.post(
            f"/posts/{post_id}/comments",
            json={"content": ""},
            headers=second_verified_user["headers"]
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_comment_too_long(self, user_with_post, second_verified_user, async_client):
        post_id = user_with_post["post"]["id"]
        response = await async_client.post(
            f"/posts/{post_id}/comments",
            json={"content": "A" * 2001},
            headers=second_verified_user["headers"]
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_comment_nonexistent_post(self, verified_user, async_client, test_comment_data):
        fake_id = str(uuid4())
        response = await async_client.post(
            f"/posts/{fake_id}/comments",
            json=test_comment_data,
            headers=verified_user["headers"]
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_comment_unauthenticated(self, user_with_post, async_client, test_comment_data):
        post_id = user_with_post["post"]["id"]
        response = await async_client.post(
            f"/posts/{post_id}/comments",
            json=test_comment_data
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_comment_unverified_user(self, user_with_post, async_client, test_comment_data):
        post_id = user_with_post["post"]["id"]
        
        from unittest.mock import patch
        new_user_data = {
            "email": "unverified_commenter@example.com",
            "username": "unverified_commenter",
            "full_name": "Unverified Commenter",
            "password": "password123"
        }
        with patch("app.services.auth_service.send_email_task"):
            await async_client.post("/auth/register", json=new_user_data)
        
        login_resp = await async_client.post(
            "/auth/login",
            data={"username": new_user_data["email"], "password": new_user_data["password"]}
        )
        token = login_resp.json()["access_token"]
        
        response = await async_client.post(
            f"/posts/{post_id}/comments",
            json=test_comment_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403


class TestListComments:

    @pytest.mark.asyncio
    async def test_list_comments_empty(self, user_with_post, async_client):
        post_id = user_with_post["post"]["id"]
        response = await async_client.get(f"/posts/{post_id}/comments")

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_comments_with_comments(self, post_with_comment, async_client):
        post_id = post_with_comment["post"]["id"]
        response = await async_client.get(f"/posts/{post_id}/comments")

        assert response.status_code == 200
        comments = response.json()
        assert len(comments) >= 1
        assert comments[0]["content"] == post_with_comment["comment"]["content"]

    @pytest.mark.asyncio
    async def test_list_comments_nonexistent_post(self, async_client):
        fake_id = str(uuid4())
        response = await async_client.get(f"/posts/{fake_id}/comments")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_comments_includes_author(self, post_with_comment, async_client):
        post_id = post_with_comment["post"]["id"]
        response = await async_client.get(f"/posts/{post_id}/comments")

        assert response.status_code == 200
        comments = response.json()
        assert "author" in comments[0]
        assert "username" in comments[0]["author"]


class TestDeleteComment:

    @pytest.mark.asyncio
    async def test_delete_comment_author(self, post_with_comment, async_client):
        post_id = post_with_comment["post"]["id"]
        comment_id = post_with_comment["comment"]["id"]
        
        response = await async_client.delete(
            f"/posts/{post_id}/comments/{comment_id}",
            headers=post_with_comment["commenter"]["headers"]
        )
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_comment_non_author(self, post_with_comment, async_client):
        post_id = post_with_comment["post"]["id"]
        comment_id = post_with_comment["comment"]["id"]
        
        response = await async_client.delete(
            f"/posts/{post_id}/comments/{comment_id}",
            headers=post_with_comment["post_owner"]["headers"]
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_comment_not_found(self, user_with_post, async_client):
        post_id = user_with_post["post"]["id"]
        fake_comment_id = str(uuid4())
        
        response = await async_client.delete(
            f"/posts/{post_id}/comments/{fake_comment_id}",
            headers=user_with_post["headers"]
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_comment_unauthenticated(self, post_with_comment, async_client):
        post_id = post_with_comment["post"]["id"]
        comment_id = post_with_comment["comment"]["id"]
        
        response = await async_client.delete(f"/posts/{post_id}/comments/{comment_id}")
        assert response.status_code == 401
