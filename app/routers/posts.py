from uuid import UUID
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app import schemas, models
from app.dependencies import (
    get_current_user,
    get_current_verified_user,
    get_post_service,
    get_comment_service,
    get_like_service
)
from app.services.post_service import PostService
from app.services.comment_service import CommentService
from app.services.like_service import LikeService

router = APIRouter()


@router.get("", response_model=schemas.PaginatedResponse)
async def list_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    service: PostService = Depends(get_post_service)
):
    results, total = await service.get_posts(
        page=page,
        page_size=page_size,
        search=search,
        date_from=date_from,
        date_to=date_to
    )

    post_responses = []
    for item in results:
        # item is a dict: {"post": Post, "likes_count": int, "comments_count": int}
        post = item["post"]
        post_responses.append(schemas.PostResponse(
            id=post.id,
            author_id=post.author_id,
            title=post.title,
            content=post.content,
            created_at=post.created_at,
            updated_at=post.updated_at,
            author=schemas.UserProfile(
                id=post.author.id,
                username=post.author.username,
                full_name=post.author.full_name
            ) if post.author else None,
            likes_count=item["likes_count"],
            comments_count=item["comments_count"]
        ))

    pages = (total + page_size - 1) // page_size if total > 0 else 1

    return schemas.PaginatedResponse(
        items=post_responses,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.post("", response_model=schemas.PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_data: schemas.PostCreate,
    current_user: models.User = Depends(get_current_verified_user),
    service: PostService = Depends(get_post_service)
):
    post = await service.create_post(post_data, current_user)
    return schemas.PostResponse(
        id=post.id,
        author_id=post.author_id,
        title=post.title,
        content=post.content,
        created_at=post.created_at,
        updated_at=post.updated_at,
        author=schemas.UserProfile(
            id=current_user.id,
            username=current_user.username,
            full_name=current_user.full_name
        ),
        likes_count=0,
        comments_count=0
    )


@router.get("/{post_id}", response_model=schemas.PostDetailResponse)
async def get_post(
    post_id: UUID,
    service: PostService = Depends(get_post_service),
    comment_service: CommentService = Depends(get_comment_service)
):
    details = await service.get_post_with_details(post_id)
    post = details["post"]
    comments = await comment_service.get_comments(post_id)

    comment_responses = [
        schemas.CommentResponse(
            id=c.id,
            post_id=c.post_id,
            author_id=c.author_id,
            content=c.content,
            created_at=c.created_at,
            author=schemas.UserProfile(
                id=c.author.id,
                username=c.author.username,
                full_name=c.author.full_name
            ) if c.author else None
        ) for c in comments
    ]

    return schemas.PostDetailResponse(
        id=post.id,
        author_id=post.author_id,
        title=post.title,
        content=post.content,
        created_at=post.created_at,
        updated_at=post.updated_at,
        author=schemas.UserProfile(
            id=post.author.id,
            username=post.author.username,
            full_name=post.author.full_name
        ) if post.author else None,
        likes_count=details["likes_count"],
        comments_count=len(comments),
        comments=comment_responses,
        likes=details["likes"]
    )


@router.patch("/{post_id}", response_model=schemas.PostResponse)
async def update_post(
    post_id: UUID,
    post_data: schemas.PostUpdate,
    current_user: models.User = Depends(get_current_verified_user),
    service: PostService = Depends(get_post_service)
):
    post = await service.update_post(post_id, post_data, current_user)
    details = await service.get_post_with_details(post_id)

    return schemas.PostResponse(
        id=post.id,
        author_id=post.author_id,
        title=post.title,
        content=post.content,
        created_at=post.created_at,
        updated_at=post.updated_at,
        author=schemas.UserProfile(
            id=post.author.id,
            username=post.author.username,
            full_name=post.author.full_name
        ) if post.author else None,
        likes_count=details["likes_count"],
        comments_count=details["comments_count"]
    )


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: UUID,
    current_user: models.User = Depends(get_current_verified_user),
    service: PostService = Depends(get_post_service)
):
    await service.delete_post(post_id, current_user)


@router.get("/{post_id}/comments", response_model=list[schemas.CommentResponse])
async def list_comments(
    post_id: UUID,
    service: PostService = Depends(get_post_service),
    comment_service: CommentService = Depends(get_comment_service)
):
    await service.get_post(post_id)
    comments = await comment_service.get_comments(post_id)

    return [
        schemas.CommentResponse(
            id=c.id,
            post_id=c.post_id,
            author_id=c.author_id,
            content=c.content,
            created_at=c.created_at,
            author=schemas.UserProfile(
                id=c.author.id,
                username=c.author.username,
                full_name=c.author.full_name
            ) if c.author else None
        ) for c in comments
    ]


@router.post("/{post_id}/comments", response_model=schemas.CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    post_id: UUID,
    comment_data: schemas.CommentCreate,
    current_user: models.User = Depends(get_current_verified_user),
    service: PostService = Depends(get_post_service),
    comment_service: CommentService = Depends(get_comment_service)
):
    await service.get_post(post_id)
    comment = await comment_service.create_comment(post_id, comment_data, current_user)

    return schemas.CommentResponse(
        id=comment.id,
        post_id=comment.post_id,
        author_id=comment.author_id,
        content=comment.content,
        created_at=comment.created_at,
        author=schemas.UserProfile(
            id=current_user.id,
            username=current_user.username,
            full_name=current_user.full_name
        )
    )


@router.delete("/{post_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    post_id: UUID,
    comment_id: UUID,
    current_user: models.User = Depends(get_current_verified_user),
    comment_service: CommentService = Depends(get_comment_service)
):
    await comment_service.delete_comment(comment_id, current_user)


@router.post("/{post_id}/like", response_model=schemas.LikeResponse, status_code=status.HTTP_201_CREATED)
async def like_post(
    post_id: UUID,
    current_user: models.User = Depends(get_current_user),
    like_service: LikeService = Depends(get_like_service)
):
    like = await like_service.like_post(post_id, current_user)
    return schemas.LikeResponse(
        id=like.id,
        user_id=like.user_id,
        post_id=like.post_id,
        created_at=like.created_at
    )


@router.delete("/{post_id}/like", status_code=status.HTTP_204_NO_CONTENT)
async def unlike_post(
    post_id: UUID,
    current_user: models.User = Depends(get_current_user),
    like_service: LikeService = Depends(get_like_service)
):
    await like_service.unlike_post(post_id, current_user)
