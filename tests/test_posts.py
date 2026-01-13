import pytest
from unittest.mock import patch
from uuid import uuid4


class TestCreatePost:

    @pytest.mark.asyncio
    async def test_create_post_verified_user(self, verified_user, async_client, test_post_data):
        response = await async_client.post(
            "/posts",
            json=test_post_data,
            headers=verified_user["headers"]
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == test_post_data["title"]
        assert data["content"] == test_post_data["content"]
        assert data["author_id"] == verified_user["user"]["id"]
        assert data["likes_count"] == 0
        assert data["comments_count"] == 0

    @pytest.mark.asyncio
    async def test_create_post_unverified_user(self, unverified_user, async_client, test_post_data):
        response = await async_client.post(
            "/posts",
            json=test_post_data,
            headers=unverified_user["headers"]
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_post_unauthenticated(self, async_client, test_post_data):
        response = await async_client.post("/posts", json=test_post_data)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_post_title_too_short(self, verified_user, async_client):
        response = await async_client.post(
            "/posts",
            json={"title": "Hi", "content": "Valid content here"},
            headers=verified_user["headers"]
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_post_title_too_long(self, verified_user, async_client):
        response = await async_client.post(
            "/posts",
            json={"title": "A" * 256, "content": "Valid content here"},
            headers=verified_user["headers"]
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_post_content_too_long(self, verified_user, async_client):
        response = await async_client.post(
            "/posts",
            json={"title": "Valid Title", "content": "A" * 10001},
            headers=verified_user["headers"]
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_post_missing_title(self, verified_user, async_client):
        response = await async_client.post(
            "/posts",
            json={"content": "Content only"},
            headers=verified_user["headers"]
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_post_missing_content(self, verified_user, async_client):
        response = await async_client.post(
            "/posts",
            json={"title": "Title only"},
            headers=verified_user["headers"]
        )
        assert response.status_code == 422


class TestGetPost:

    @pytest.mark.asyncio
    async def test_get_post_success(self, user_with_post, async_client):
        post_id = user_with_post["post"]["id"]
        response = await async_client.get(f"/posts/{post_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == post_id
        assert data["title"] == user_with_post["post"]["title"]
        assert "author" in data
        assert "comments" in data
        assert "likes" in data

    @pytest.mark.asyncio
    async def test_get_post_not_found(self, async_client):
        fake_id = str(uuid4())
        response = await async_client.get(f"/posts/{fake_id}")

        assert response.status_code == 404
        assert "Post not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_post_includes_author_info(self, user_with_post, async_client):
        post_id = user_with_post["post"]["id"]
        response = await async_client.get(f"/posts/{post_id}")

        assert response.status_code == 200
        author = response.json()["author"]
        assert author["username"] == user_with_post["data"]["username"]
        assert "full_name" in author


class TestUpdatePost:

    @pytest.mark.asyncio
    async def test_update_post_author(self, user_with_post, async_client):
        post_id = user_with_post["post"]["id"]
        response = await async_client.patch(
            f"/posts/{post_id}",
            json={"title": "Updated Title"},
            headers=user_with_post["headers"]
        )

        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"

    @pytest.mark.asyncio
    async def test_update_post_non_author(self, user_with_post, second_verified_user, async_client):
        post_id = user_with_post["post"]["id"]
        response = await async_client.patch(
            f"/posts/{post_id}",
            json={"title": "Hacked Title"},
            headers=second_verified_user["headers"]
        )

        assert response.status_code == 403
        assert "Not authorized" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_post_not_found(self, verified_user, async_client):
        fake_id = str(uuid4())
        response = await async_client.patch(
            f"/posts/{fake_id}",
            json={"title": "New Title"},
            headers=verified_user["headers"]
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_post_partial(self, user_with_post, async_client):
        post_id = user_with_post["post"]["id"]
        original_title = user_with_post["post"]["title"]
        
        response = await async_client.patch(
            f"/posts/{post_id}",
            json={"content": "Brand new content"},
            headers=user_with_post["headers"]
        )

        assert response.status_code == 200
        assert response.json()["title"] == original_title
        assert response.json()["content"] == "Brand new content"

    @pytest.mark.asyncio
    async def test_update_post_unauthenticated(self, user_with_post, async_client):
        post_id = user_with_post["post"]["id"]
        response = await async_client.patch(
            f"/posts/{post_id}",
            json={"title": "New Title"}
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_post_invalid_title(self, user_with_post, async_client):
        post_id = user_with_post["post"]["id"]
        response = await async_client.patch(
            f"/posts/{post_id}",
            json={"title": "Hi"},
            headers=user_with_post["headers"]
        )
        assert response.status_code == 422


class TestDeletePost:

    @pytest.mark.asyncio
    async def test_delete_post_author(self, user_with_post, async_client):
        post_id = user_with_post["post"]["id"]
        response = await async_client.delete(
            f"/posts/{post_id}",
            headers=user_with_post["headers"]
        )

        assert response.status_code == 204

        get_response = await async_client.get(f"/posts/{post_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_post_non_author(self, user_with_post, second_verified_user, async_client):
        post_id = user_with_post["post"]["id"]
        response = await async_client.delete(
            f"/posts/{post_id}",
            headers=second_verified_user["headers"]
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_post_not_found(self, verified_user, async_client):
        fake_id = str(uuid4())
        response = await async_client.delete(
            f"/posts/{fake_id}",
            headers=verified_user["headers"]
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_post_unauthenticated(self, user_with_post, async_client):
        post_id = user_with_post["post"]["id"]
        response = await async_client.delete(f"/posts/{post_id}")
        assert response.status_code == 401


class TestListPosts:

    @pytest.mark.asyncio
    async def test_list_posts_empty(self, async_client):
        response = await async_client.get("/posts")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_posts_with_posts(self, user_with_post, async_client):
        response = await async_client.get("/posts")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    @pytest.mark.asyncio
    async def test_list_posts_pagination(self, verified_user, async_client, test_post_data):
        for i in range(5):
            post_data = {"title": f"Post number {i+1}", "content": f"Content for post {i+1}"}
            await async_client.post("/posts", json=post_data, headers=verified_user["headers"])

        response = await async_client.get("/posts?page=1&page_size=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total"] == 5
        assert data["pages"] == 3

    @pytest.mark.asyncio
    async def test_list_posts_search(self, verified_user, async_client):
        await async_client.post(
            "/posts",
            json={"title": "Python Programming", "content": "Learn Python basics"},
            headers=verified_user["headers"]
        )
        await async_client.post(
            "/posts",
            json={"title": "Cooking Recipes", "content": "Delicious meals"},
            headers=verified_user["headers"]
        )

        response = await async_client.get("/posts?search=Python")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any("Python" in item["title"] for item in data["items"])

    @pytest.mark.asyncio
    async def test_list_posts_includes_author(self, user_with_post, async_client):
        response = await async_client.get("/posts")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert "author" in data["items"][0]
        assert "username" in data["items"][0]["author"]
