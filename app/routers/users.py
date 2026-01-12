from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .. import models, schemas
from ..dependencies import get_db

from app.services.user_service import UserService
from app.dependencies import get_user_service

router = APIRouter()


@router.post("/", response_model=schemas.User)
async def create_user(
    user: schemas.UserCreate, 
    service: UserService = Depends(get_user_service) # <--- Clean Injection
):
    # One line to rule them all
    return await service.register_user(user)

@router.post("/verify")
async def verify_user(req: schemas.VerificationRequest, db: AsyncSession = Depends(get_db)):
    # 1. Find user by email
    result = await db.execute(select(models.User).filter(models.User.email == req.email))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # 2. Check if already verified
    if user.is_verified:
        return {"message": "User already verified"}
        
    # 3. Check code
    if user.verification_code != req.code:
        raise HTTPException(status_code=400, detail="Invalid verification code")
        
    # 4. Verify!
    user.is_verified = True
    user.verification_code = None # Optional: Clear the code after use
    await db.commit()
    
    return {"message": "Account verified successfully"}