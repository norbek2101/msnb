from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query

from app import schemas, models
from app.dependencies import get_db
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

router = APIRouter()


@router.post("/cleanup-unverified", response_model=schemas.MessageResponse)
async def cleanup_unverified_users(
    hours: int = Query(default=None),
    db: AsyncSession = Depends(get_db)
):
    cleanup_hours = hours if hours is not None else settings.UNVERIFIED_USER_CLEANUP_HOURS
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=cleanup_hours)

    result = await db.execute(
        select(models.User).filter(
            models.User.is_verified == False,
            models.User.created_at < cutoff_time
        )
    )
    users_to_delete = result.scalars().all()
    count = len(users_to_delete)

    for user in users_to_delete:
        await db.delete(user)

    await db.commit()

    return schemas.MessageResponse(
        message=f"Deleted {count} unverified users older than {cleanup_hours} hours"
    )
