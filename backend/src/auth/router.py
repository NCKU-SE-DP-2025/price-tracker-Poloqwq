from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from src.auth.dependencies import get_auth_service, get_current_user
from src.auth.service import AuthService
from src.auth.schemas import UserAuthSchema
from src.auth.config import TOKEN_EXPIRE_MINUTES

router = APIRouter()

@router.post("/register")
def create_user(
    user_data: UserAuthSchema,
    auth_service: AuthService = Depends(get_auth_service)
):
    user = auth_service.create_user(user_data.username, user_data.password)
    return {"username": user.username, "id": user.id}


@router.post("/login")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    user = auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = auth_service.create_access_token(
        username=user.username,
        expires_delta=timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me")
def read_users_me(user = Depends(get_current_user)):
    return {"username": user.username}