from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct, desc
from sqlalchemy.orm import selectinload
from app import models

class FeedRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_feed(
        self,
        page: int = 1,
        page_size: int = 10
    ) -> tuple[list[dict], int]:
        """
        Fetches feed: List of users with their recent posts, efficiently.
        """
        # Count total users
        count_stmt = select(func.count(models.User.id))
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Fetch users paginated
        # We also want their posts. 
        # The original logic was: Users -> Posts -> Likes for EACH post.
        # This is tricky to optmize 100% in one query if we want nested structure "User -> [Posts]".
        # But we can assume we load users and perform selectinload for posts.
        # AND selectinload for posts.likes might be heavy.
        
        # Strategy:
        # Load Users.
        # Load Posts for these users (selectinload).
        # Load Likes/Counts for these posts (selectinload or strategy).
        
        # Since this is a "feed" of Users ??? (Wait, the original code is weird).
        # Original Feed: 
        # result = await db.execute(select(models.User).options(selectinload(models.User.posts))...)
        # It displays "FeedUserResponse" -> username, posts[].
        # So it's a feed of USERS and their posts? That's an unusual feed, but okay.
        
        stmt = (
            select(models.User)
            .options(
                selectinload(models.User.posts).selectinload(models.Post.likes) # Optimizes the likes fetching mostly
            )
            .order_by(models.User.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        
        result = await self.db.execute(stmt)
        users = result.scalars().all()
        
        # We need to format this for the service.
        # To avoid N+1 on "likes list" in the loop, we used selectinload above.
        # selectinload(models.Post.likes) checks the relationship.
        # If we need just IDs, it loads the full Like objects. 
        # It's better than N queries.
        
        return list(users), total
