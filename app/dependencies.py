from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import decode_token
from app import models
from app.database import AsyncSessionLocal
from app.repositories.user_repository import UserRepository
from app.repositories.post_repository import PostRepository
from app.repositories.comment_repository import CommentRepository
from app.repositories.like_repository import LikeRepository
from app.services.user_service import UserService
from app.services.auth_service import AuthService
from app.services.post_service import PostService
from app.services.comment_service import CommentService
from app.services.like_service import LikeService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise credentials_exception

    result = await db.execute(select(models.User).filter(models.User.id == user_id))
    user = result.scalars().first()

    if user is None:
        raise credentials_exception

    return user


async def get_current_verified_user(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required"
        )
    return current_user


def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_post_repository(db: AsyncSession = Depends(get_db)) -> PostRepository:
    return PostRepository(db)


def get_comment_repository(db: AsyncSession = Depends(get_db)) -> CommentRepository:
    return CommentRepository(db)


def get_like_repository(db: AsyncSession = Depends(get_db)) -> LikeRepository:
    return LikeRepository(db)


def get_user_service(repo: UserRepository = Depends(get_user_repository)) -> UserService:
    return UserService(repo)


def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
    db: AsyncSession = Depends(get_db)
) -> AuthService:
    return AuthService(user_repo, db)


def get_post_service(
    post_repo: PostRepository = Depends(get_post_repository),
    like_repo: LikeRepository = Depends(get_like_repository)
) -> PostService:
    return PostService(post_repo, like_repo)


def get_comment_service(
    comment_repo: CommentRepository = Depends(get_comment_repository)
) -> CommentService:
    return CommentService(comment_repo)


def get_like_service(
    like_repo: LikeRepository = Depends(get_like_repository),
    post_repo: PostRepository = Depends(get_post_repository)
) -> LikeService:
    return LikeService(like_repo, post_repo)