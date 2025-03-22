from fastapi import APIRouter, HTTPException, status, Response, BackgroundTasks, Form, Depends, Cookie
from sqlmodel import Session, select
from datetime import timedelta

from ..database import engine
from .. import models
from ..auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_user,
)
from ..services import webui


auth_router = APIRouter()

@auth_router.post("/api/register", response_model=models.UserRead)
async def register(user: models.UserCreate, background_tasks: BackgroundTasks):
    with Session(engine) as session:
        statement = select(models.User).where(models.User.email == user.email)
        if session.exec(statement).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        db_user = models.User(
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            birthdate=user.birthdate,
            hashed_password=get_password_hash(user.password)
        )
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        
        background_tasks.add_task(webui.create_webui_user, user.email, user.password, user.first_name + " " + user.last_name)

        return db_user

@auth_router.post("/api/token")
async def login(response: Response, email: str = Form(), password: str = Form()):
    with Session(engine) as session:
        statement = select(models.User).where(models.User.email == email)
        user = session.exec(statement).first()
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        response.set_cookie(
            key="token",
            value=access_token,
            httponly=True,
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        return {"access_token": access_token, "token_type": "bearer"}

@auth_router.get("/api/me", response_model=models.UserRead)
async def get_current_user_info(current_user: models.User = Depends(get_current_user)):
    return current_user
