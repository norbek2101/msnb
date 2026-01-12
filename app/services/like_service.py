from uuid import UUID
from fastapi import HTTPException, status

from app import models
from app.repositories.like_repository import LikeRepository
from app.repositories.post_repository import PostRepository


class LikeService:
    def __init__(self, like_repo: LikeRepository, post_repo: PostRepository):
        self.like_repo = like_repo
        self.post_repo = post_repo

    async def like_post(self, post_id: UUID, user: models.User) -> models.Like:
        post = await self.post_repo.get_by_id(post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )

        if post.author_id == user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot like your own post"
            )

        existing_like = await self.like_repo.get_by_user_and_post(user.id, post_id)
        if existing_like:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already liked this post"
            )

        new_like = models.Like(
            user_id=user.id,
            post_id=post_id
        )
        return await self.like_repo.create(new_like)

    async def unlike_post(self, post_id: UUID, user: models.User) -> None:
        post = await self.post_repo.get_by_id(post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )

        existing_like = await self.like_repo.get_by_user_and_post(user.id, post_id)
        if not existing_like:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Like not found"
            )

        await self.like_repo.delete(existing_like)
