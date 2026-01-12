from fastapi import APIRouter, Depends, HTTPException, status, Request 
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .. import models, schemas
from ..dependencies import get_db
from app.core import security
from app.core.limiter import limiter

router = APIRouter()

@router.post("/login", response_model=schemas.Token)
@limiter.limit("5/minute")
async def login_for_access_token(
    request: Request,  
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(models.User).filter(models.User.email == form_data.username)
    )
    user = result.scalars().first()
    
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = security.create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}