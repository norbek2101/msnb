from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app import models


class CommentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, comment_id: UUID) -> models.Comment | None:
        result = await self.db.execute(
            select(models.Comment).filter(models.Comment.id == comment_id)
        )
        return result.scalars().first()

    async def get_by_post_id(self, post_id: UUID) -> list[models.Comment]:
        result = await self.db.execute(
            select(models.Comment)
            .filter(models.Comment.post_id == post_id)
            .order_by(models.Comment.created_at.asc())
        )
        return list(result.scalars().all())

    async def create(self, comment: models.Comment) -> models.Comment:
        self.db.add(comment)
        await self.db.commit()
        await self.db.refresh(comment)
        return comment

    async def delete(self, comment: models.Comment) -> None:
        await self.db.delete(comment)
        await self.db.commit()
