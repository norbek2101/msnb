from uuid import UUID
from fastapi import HTTPException, status

from app import models, schemas
from app.repositories.comment_repository import CommentRepository


class CommentService:
    def __init__(self, comment_repo: CommentRepository):
        self.comment_repo = comment_repo

    async def get_comments(self, post_id: UUID) -> list[models.Comment]:
        return await self.comment_repo.get_by_post_id(post_id)

    async def create_comment(
        self,
        post_id: UUID,
        comment_data: schemas.CommentCreate,
        author: models.User
    ) -> models.Comment:
        new_comment = models.Comment(
            post_id=post_id,
            author_id=author.id,
            content=comment_data.content
        )
        return await self.comment_repo.create(new_comment)

    async def delete_comment(
        self,
        comment_id: UUID,
        current_user: models.User
    ) -> None:
        comment = await self.comment_repo.get_by_id(comment_id)

        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )

        if comment.author_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this comment"
            )

        await self.comment_repo.delete(comment)
