from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select 
from app.core import security
from app import models
from app.database import AsyncSessionLocal
import jwt
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        token_data = payload.get("sub")
        
        if token_data is None:
            raise credentials_exception
            
        user_id = int(token_data)
    except (jwt.PyJWTError, ValueError):
        raise credentials_exception
        
    result = await db.execute(select(models.User).filter(models.User.id == user_id))
    user = result.scalars().first() 
    
    if user is None:
        raise credentials_exception
        
    return user

def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

def get_user_service(repo: UserRepository = Depends(get_user_repository)) -> UserService:
    return UserService(repo)