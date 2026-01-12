from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.limiter import limiter
from app.routers import auth, users, posts, feed, admin

app = FastAPI(
    title="Mini Social Network API",
    description="Backend API for a mini social network with users, posts, comments, and likes",
    version="1.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(posts.router, prefix="/posts", tags=["Posts"])
app.include_router(feed.router, prefix="/all", tags=["Feed"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok"}