from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app import models

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> models.User | None:
        result = await self.db.execute(select(models.User).filter(models.User.email == email))
        return result.scalars().first()

    async def get_by_id(self, user_id: int) -> models.User | None:
        result = await self.db.execute(select(models.User).filter(models.User.id == user_id))
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