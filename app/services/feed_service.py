from app.repositories.feed_repository import FeedRepository
from app import schemas

class FeedService:
    def __init__(self, feed_repo: FeedRepository):
        self.feed_repo = feed_repo

    async def get_feed(self, page: int = 1, page_size: int = 10) -> tuple[list[schemas.FeedUserResponse], int]:
        users, total = await self.feed_repo.get_feed(page, page_size)

        feed_items = []
        for user in users:
            posts_data = []
            if user.posts:
                # user.posts are loaded.
                # Sort them by date just in case, though usually DB order is preserved if specified.
                # The repo ordered Users, but not necessarily posts within user (unless defined in relationship or query).
                # Default relationship usually doesn't sort.
                # Let's sort in python to be safe, or just take them as is if order doesn't matter much inside the sub-list.
                sorted_posts = sorted(user.posts, key=lambda p: p.created_at, reverse=True)
                
                for post in sorted_posts:
                    # Extract like user_ids from the loaded relationship
                    # post.likes is loaded via selectinload.
                    like_user_ids = [like.user_id for like in post.likes]
                    
                    posts_data.append(schemas.FeedPostResponse(
                        id=post.id,
                        title=post.title,
                        content=post.content,
                        likes=like_user_ids
                    ))

            feed_items.append(schemas.FeedUserResponse(
                username=user.username,
                posts=posts_data
            ))
            
        return feed_items, total
