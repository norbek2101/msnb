from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from fastapi import HTTPException, status

from app import models, schemas
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    generate_verification_token,
    get_verification_token_expiry
)
from app.repositories.user_repository import UserRepository
from app.tasks import send_email_task


class AuthService:
    def __init__(self, user_repo: UserRepository, db: AsyncSession):
        self.user_repo = user_repo
        self.db = db

    async def register(self, user_data: schemas.UserCreate) -> models.User:
        existing_email = await self.user_repo.get_by_email(user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        existing_username = await self.user_repo.get_by_username(user_data.username)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

        hashed_pwd = get_password_hash(user_data.password)

        new_user = models.User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            password_hash=hashed_pwd,
            is_verified=False
        )

        saved_user = await self.user_repo.create(new_user)

        token = generate_verification_token()
        expires_at = get_verification_token_expiry()

        verification_token = models.EmailVerificationToken(
            user_id=saved_user.id,
            token=token,
            expires_at=expires_at
        )
        self.db.add(verification_token)
        await self.db.commit()

        send_email_task.delay(saved_user.email, token)

        return saved_user

    async def login(self, login_data: schemas.LoginRequest) -> schemas.Token:
        if not login_data.email and not login_data.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email or username is required"
            )

        user = None
        if login_data.email:
            user = await self.user_repo.get_by_email(login_data.email)
        elif login_data.username:
            user = await self.user_repo.get_by_username(login_data.username)

        if not user or not verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = create_access_token(data={"sub": str(user.id)})
        return schemas.Token(access_token=access_token)

    async def verify_email(self, token: str) -> models.User:
        result = await self.db.execute(
            select(models.EmailVerificationToken)
            .filter(models.EmailVerificationToken.token == token)
        )
        verification_token = result.scalars().first()

        if not verification_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token"
            )

        if verification_token.expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification token has expired"
            )

        user = await self.user_repo.get_by_id(verification_token.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user.is_verified = True
        await self.db.commit()

        await self.db.execute(
            delete(models.EmailVerificationToken)
            .where(models.EmailVerificationToken.user_id == user.id)
        )
        await self.db.commit()

        return user

    async def resend_verification(self, user: models.User) -> None:
        if user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already verified"
            )

        await self.db.execute(
            delete(models.EmailVerificationToken)
            .where(models.EmailVerificationToken.user_id == user.id)
        )

        token = generate_verification_token()
        expires_at = get_verification_token_expiry()

        verification_token = models.EmailVerificationToken(
            user_id=user.id,
            token=token,
            expires_at=expires_at
        )
        self.db.add(verification_token)
        await self.db.commit()

        send_email_task.delay(user.email, token)
