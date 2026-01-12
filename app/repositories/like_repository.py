from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app import models


class LikeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_and_post(self, user_id: UUID, post_id: UUID) -> models.Like | None:
        result = await self.db.execute(
            select(models.Like).filter(
                models.Like.user_id == user_id,
                models.Like.post_id == post_id
            )
        )
        return result.scalars().first()

    async def get_by_post_id(self, post_id: UUID) -> list[models.Like]:
        result = await self.db.execute(
            select(models.Like).filter(models.Like.post_id == post_id)
        )
        return list(result.scalars().all())

    async def count_by_post_id(self, post_id: UUID) -> int:
        result = await self.db.execute(
            select(models.Like).filter(models.Like.post_id == post_id)
        )
        return len(result.scalars().all())

    async def create(self, like: models.Like) -> models.Like:
        self.db.add(like)
        await self.db.commit()
        await self.db.refresh(like)
        return like

    async def delete(self, like: models.Like) -> None:
        await self.db.delete(like)
        await self.db.commit()

    async def get_user_ids_by_post(self, post_id: UUID) -> list[UUID]:
        result = await self.db.execute(
            select(models.Like.user_id).filter(models.Like.post_id == post_id)
        )
        return list(result.scalars().all())
