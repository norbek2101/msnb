from typing import Optional
from fastapi import APIRouter, Depends, Query

from app import schemas
from app.dependencies import get_feed_service
from app.services.feed_service import FeedService

router = APIRouter()


@router.get("", response_model=schemas.PaginatedResponse)
async def get_feed(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    service: FeedService = Depends(get_feed_service)
):
    feed_items, total = await service.get_feed(page, page_size)

    pages = (total + page_size - 1) // page_size if total > 0 else 1

    return schemas.PaginatedResponse(
        items=feed_items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )
