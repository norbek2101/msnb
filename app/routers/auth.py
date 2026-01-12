from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas, models
from app.dependencies import get_db, get_auth_service, get_current_user
from app.services.auth_service import AuthService
from app.core.limiter import limiter

router = APIRouter()


@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: schemas.UserCreate,
    service: AuthService = Depends(get_auth_service)
):
    user = await service.register(user_data)
    return user


@router.post("/login", response_model=schemas.Token)
@limiter.limit("5/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service)
):
    login_data = schemas.LoginRequest(
        email=form_data.username if "@" in form_data.username else None,
        username=form_data.username if "@" not in form_data.username else None,
        password=form_data.password
    )
    return await service.login(login_data)


@router.get("/me", response_model=schemas.UserResponse)
async def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.get("/verify-email", response_model=schemas.MessageResponse)
async def verify_email(
    token: str = Query(...),
    service: AuthService = Depends(get_auth_service)
):
    await service.verify_email(token)
    return schemas.MessageResponse(message="Email verified successfully")


@router.post("/resend-verification", response_model=schemas.MessageResponse)
async def resend_verification(
    current_user: models.User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service)
):
    await service.resend_verification(current_user)
    return schemas.MessageResponse(message="Verification email sent")