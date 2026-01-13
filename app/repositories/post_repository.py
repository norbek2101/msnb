from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app import models


class PostRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, post_id: UUID) -> models.Post | None:
        result = await self.db.execute(
            select(models.Post)
            .options(
                selectinload(models.Post.author),
                selectinload(models.Post.comments).selectinload(models.Comment.author),
                selectinload(models.Post.likes)
            )
            .filter(models.Post.id == post_id)
        )
        return result.scalars().first()

    async def get_list(
        self,
        page: int = 1,
        page_size: int = 10,
        search: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None
    ) -> tuple[list[models.Post], int]:
        query = select(models.Post).options(selectinload(models.Post.author))

        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                (models.Post.title.ilike(search_filter)) |
                (models.Post.content.ilike(search_filter))
            )

        if date_from:
            query = query.filter(models.Post.created_at >= date_from)

        if date_to:
            query = query.filter(models.Post.created_at <= date_to)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(models.Post.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        posts = result.scalars().all()

        return list(posts), total

    async def create(self, post: models.Post) -> models.Post:
        self.db.add(post)
        await self.db.commit()
        await self.db.refresh(post)
        return post

    async def update(self, post: models.Post) -> models.Post:
        await self.db.commit()
        await self.db.refresh(post)
        return post

    async def delete(self, post: models.Post) -> None:
        await self.db.delete(post)
        await self.db.commit()

    async def get_posts_by_author(self, author_id: UUID) -> list[models.Post]:
        result = await self.db.execute(
            select(models.Post)
            .options(selectinload(models.Post.author))
            .filter(models.Post.author_id == author_id)
        )
        return list(result.scalars().all())
