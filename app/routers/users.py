from fastapi import APIRouter, Depends, HTTPException, status

from app import schemas, models
from app.dependencies import get_current_user, get_user_repository
from app.repositories.user_repository import UserRepository

router = APIRouter()


@router.patch("/me", response_model=schemas.UserResponse)
async def update_profile(
    user_data: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    if user_data.username is not None:
        existing = await user_repo.get_by_username(user_data.username)
        if existing and existing.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        current_user.username = user_data.username

    if user_data.full_name is not None:
        current_user.full_name = user_data.full_name

    updated_user = await user_repo.update(current_user)
    return updated_user


@router.get("/me", response_model=schemas.UserResponse)
async def get_profile(current_user: models.User = Depends(get_current_user)):
    return current_user