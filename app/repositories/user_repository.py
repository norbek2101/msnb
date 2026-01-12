from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app import models


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> models.User | None:
        result = await self.db.execute(
            select(models.User).filter(models.User.email == email)
        )
        return result.scalars().first()

    async def get_by_username(self, username: str) -> models.User | None:
        result = await self.db.execute(
            select(models.User).filter(models.User.username == username)
        )
        return result.scalars().first()

    async def get_by_id(self, user_id: UUID) -> models.User | None:
        result = await self.db.execute(
            select(models.User).filter(models.User.id == user_id)
        )
        return result.scalars().first()

    async def create(self, user: models.User) -> models.User:
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update(self, user: models.User) -> models.User:
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete(self, user: models.User) -> None:
        await self.db.delete(user)
        await self.db.commit()

    async def get_all_with_posts(
        self,
        page: int = 1,
        page_size: int = 10
    ) -> tuple[list[models.User], int]:
        count_result = await self.db.execute(select(models.User))
        total = len(count_result.scalars().all())

        result = await self.db.execute(
            select(models.User)
            .order_by(models.User.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        users = result.scalars().all()
        return list(users), total