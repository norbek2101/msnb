from uuid import UUID
from datetime import datetime
from fastapi import HTTPException, status

from app import models, schemas
from app.repositories.post_repository import PostRepository
from app.repositories.like_repository import LikeRepository


class PostService:
    def __init__(self, post_repo: PostRepository, like_repo: LikeRepository):
        self.post_repo = post_repo
        self.like_repo = like_repo

    async def get_posts(
        self,
        page: int = 1,
        page_size: int = 10,
        search: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None
    ) -> tuple[list[dict], int]:
        return await self.post_repo.get_list(
            page=page,
            page_size=page_size,
            search=search,
            date_from=date_from,
            date_to=date_to
        )

    async def get_post(self, post_id: UUID) -> models.Post:
        # Note: This might fetch just the post without counts if the repo changes, 
        # but for now get_by_id returns a dict. We need to handle that carefully.
        # Actually, let's keep a method in repo for "just post" if implementation logic needs it,
        # or extract it from the result.
        # Looking at original code, get_post was used for internal logic (update/delete).
        # We need to make sure we can still get the model object.
        
        # The repo.get_by_id now returns a dict or None.
        result = await self.post_repo.get_by_id(post_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )
        return result["post"]

    async def create_post(
        self,
        post_data: schemas.PostCreate,
        author: models.User
    ) -> models.Post:
        new_post = models.Post(
            author_id=author.id,
            title=post_data.title,
            content=post_data.content
        )
        return await self.post_repo.create(new_post)

    async def update_post(
        self,
        post_id: UUID,
        post_data: schemas.PostUpdate,
        current_user: models.User
    ) -> models.Post:
        post = await self.get_post(post_id)

        if post.author_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to edit this post"
            )

        if post_data.title is not None:
            post.title = post_data.title
        if post_data.content is not None:
            post.content = post_data.content

        return await self.post_repo.update(post)

    async def delete_post(self, post_id: UUID, current_user: models.User) -> None:
        post = await self.get_post(post_id)

        if post.author_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this post"
            )

        await self.post_repo.delete(post)

    async def get_post_with_details(self, post_id: UUID) -> dict:
        result = await self.post_repo.get_by_id(post_id)
        if not result:
             raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )
        
        # We need 'likes' list for the detail view specifically?
        # The original code returned "likes": likes (list of IDs).
        # The optimization returns counts. 
        # If the frontend needs the LIST of likes (e.g. to show avatars), we need that.
        # But usually 'likes_count' is enough, and 'is_liked' (by me).
        # Original router used `details["likes"]` in `get_post` router.
        # Let's check `schemas.PostDetailResponse`.
        
        # We might need to fetch likes separately if the schema demands the list of likes.
        # Yes, schema might demand it.
        # The repo get_by_id now has count.
        # We can fetch likes list if needed.
        
        likes_ids = await self.like_repo.get_user_ids_by_post(post_id)
        
        result["likes"] = likes_ids
        # Ensure counts are correct (repo count should match len(likes_ids) usually, but repo count is faster)
        
        return result
