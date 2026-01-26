from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct, desc
from sqlalchemy.orm import selectinload
from app import models


class PostRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, post_id: UUID) -> dict | None:
        """
        Fetches a single post with its like and comment counts.
        Returns a dictionary with 'post', 'likes_count', and 'comments_count'.
        """
        stmt = (
            select(
                models.Post,
                func.count(distinct(models.Like.id)).label("likes_count"),
                func.count(distinct(models.Comment.id)).label("comments_count"),
            )
            .outerjoin(models.Like, models.Post.id == models.Like.post_id)
            .outerjoin(models.Comment, models.Post.id == models.Comment.post_id)
            .options(
                selectinload(models.Post.author),
                # We don't selectinload likes/comments mostly because we have counts,
                # but if the frontend needs the actual list, we might need a separate query or strictly limited load.
                # For details view, we might want the actual comments, but let's stick to the base requirement of counts first.
                # The service can fetch comments separately if needed (it does).
            )
            .filter(models.Post.id == post_id)
            .group_by(models.Post.id)
        )

        result = await self.db.execute(stmt)
        row = result.first()
        if not row:
            return None
        
        post, likes_count, comments_count = row
        return {
            "post": post,
            "likes_count": likes_count,
            "comments_count": comments_count
        }

    async def get_list(
        self,
        page: int = 1,
        page_size: int = 10,
        search: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None
    ) -> tuple[list[dict], int]:
        """
        Fetches a paginated list of posts with counts.
        Returns (list_of_dicts_with_counts, total_count).
        """
        # Base query for filtering
        base_query = select(models.Post)

        if search:
            search_filter = f"%{search}%"
            base_query = base_query.filter(
                (models.Post.title.ilike(search_filter)) |
                (models.Post.content.ilike(search_filter))
            )

        if date_from:
            base_query = base_query.filter(models.Post.created_at >= date_from)

        if date_to:
            base_query = base_query.filter(models.Post.created_at <= date_to)

        # Count total matches (efficiently)
        count_stmt = select(func.count()).select_from(base_query.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Main Data Query with Aggregation
        # We need to apply the same filters to the main query
        stmt = (
            select(
                models.Post,
                func.count(distinct(models.Like.id)).label("likes_count"),
                func.count(distinct(models.Comment.id)).label("comments_count"),
            )
            .outerjoin(models.Like, models.Post.id == models.Like.post_id)
            .outerjoin(models.Comment, models.Post.id == models.Comment.post_id)
            .options(selectinload(models.Post.author))
            .group_by(models.Post.id)
        )

        # Apply filters again (or construct efficiently)
        # Note: In SQLAlchemy 1.4/2.0+ reuse of the where clauses is easy.
        # But since I constructed base_query separately, I'll re-apply filters to stmt.
        # A cleaner way is to build the conditions first.
        
        if search:
            search_filter = f"%{search}%"
            stmt = stmt.filter(
                (models.Post.title.ilike(search_filter)) |
                (models.Post.content.ilike(search_filter))
            )
        if date_from:
            stmt = stmt.filter(models.Post.created_at >= date_from)
        if date_to:
            stmt = stmt.filter(models.Post.created_at <= date_to)

        stmt = stmt.order_by(models.Post.created_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(stmt)
        rows = result.all()

        # Convert rows to list of dicts/structure service expects
        results = []
        for row in rows:
            post, likes_count, comments_count = row
            results.append({
                "post": post,
                "likes_count": likes_count,
                "comments_count": comments_count
            })

        return results, total

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
        # Keeping this simple for now as it's likely internal or less used. 
        # But ideally should also have counts if used in a list view.
        result = await self.db.execute(
            select(models.Post)
            .options(selectinload(models.Post.author))
            .filter(models.Post.author_id == author_id)
        )
        return list(result.scalars().all())
