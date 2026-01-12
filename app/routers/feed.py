from typing import Optional
from fastapi import APIRouter, Depends, Query

from app import schemas, models
from app.dependencies import get_db, get_user_repository, get_like_repository
from app.repositories.user_repository import UserRepository
from app.repositories.like_repository import LikeRepository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

router = APIRouter()


@router.get("", response_model=schemas.PaginatedResponse)
async def get_feed(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    like_repo: LikeRepository = Depends(get_like_repository)
):
    count_result = await db.execute(select(models.User))
    total = len(count_result.scalars().all())

    result = await db.execute(
        select(models.User)
        .options(selectinload(models.User.posts))
        .order_by(models.User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    users = result.scalars().all()

    feed_items = []
    for user in users:
        posts_data = []
        for post in user.posts:
            likes = await like_repo.get_user_ids_by_post(post.id)
            posts_data.append(schemas.FeedPostResponse(
                id=post.id,
                title=post.title,
                content=post.content,
                likes=likes
            ))

        feed_items.append(schemas.FeedUserResponse(
            username=user.username,
            posts=posts_data
        ))

    pages = (total + page_size - 1) // page_size if total > 0 else 1

    return schemas.PaginatedResponse(
        items=feed_items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )
