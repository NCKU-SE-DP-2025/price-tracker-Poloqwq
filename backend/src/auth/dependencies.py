from fastapi import Depends
from sqlalchemy.orm import Session
from src.auth.service import AuthService
from src.database import get_db
from src.auth.config import JWT_SECRET_KEY
from src.auth.schemas import oauth2_scheme
from fastapi import HTTPException


def get_auth_service(db: Session = Depends(get_db)):
    return AuthService(db, JWT_SECRET_KEY)

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    auth_service = AuthService(db, JWT_SECRET_KEY)
    user = auth_service.get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user