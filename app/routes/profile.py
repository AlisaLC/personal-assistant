
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from ..database import engine
from .. import models
from ..auth import (
    get_current_user,
    get_password_hash,
)


profile_router = APIRouter()

@profile_router.get("/api/profile", response_model=models.UserRead)
async def get_profile(current_user: models.User = Depends(get_current_user)):
    """Get current user's profile"""
    return current_user

@profile_router.put("/api/profile", response_model=models.UserRead)
async def update_profile(
    user_update: models.UserCreate,
    current_user: models.User = Depends(get_current_user)
):
    """Update current user's profile"""
    with Session(engine) as session:
        statement = select(models.User).where(models.User.id == current_user.id)
        db_user = session.exec(statement).first()
        
        db_user.first_name = user_update.first_name
        db_user.last_name = user_update.last_name
        db_user.birthdate = user_update.birthdate
        
        if user_update.password:
            db_user.hashed_password = get_password_hash(user_update.password)
        
        session.commit()
        session.refresh(db_user)
        return db_user
