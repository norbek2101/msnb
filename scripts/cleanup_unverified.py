import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

import sys
sys.path.insert(0, '/Users/norbek/projects/interview/msnb')

from app.core.config import settings
from app import models


async def cleanup_unverified_users(hours: int = None):
    cleanup_hours = hours if hours is not None else settings.UNVERIFIED_USER_CLEANUP_HOURS
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=cleanup_hours)

    database_url = settings.DATABASE_URL
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        result = await session.execute(
            select(models.User).filter(
                models.User.is_verified == False,
                models.User.created_at < cutoff_time
            )
        )
        users_to_delete = result.scalars().all()
        count = len(users_to_delete)

        for user in users_to_delete:
            await session.delete(user)

        await session.commit()

        print(f"Deleted {count} unverified users older than {cleanup_hours} hours")

    await engine.dispose()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Cleanup unverified users")
    parser.add_argument("--hours", type=int, default=None, help="Hours threshold for cleanup")
    args = parser.parse_args()

    asyncio.run(cleanup_unverified_users(args.hours))
