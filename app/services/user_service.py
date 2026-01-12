from fastapi import HTTPException, status
from app import models, schemas
from app.core.security import get_password_hash
from app.repositories.user_repository import UserRepository
from app.tasks import send_email_task
import random
import string

class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def _generate_code(self, length=6):
        return ''.join(random.choices(string.digits, k=length))

    async def register_user(self, user_data: schemas.UserCreate) -> models.User:
        existing_user = await self.user_repo.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        hashed_pwd = get_password_hash(user_data.password)
        verification_code = self._generate_code()

        new_user = models.User(
            email=user_data.email,
            hashed_password=hashed_pwd,
            is_verified=False,
            verification_code=verification_code
        )

        saved_user = await self.user_repo.create(new_user)

        send_email_task.delay(saved_user.email, verification_code)

        return saved_user