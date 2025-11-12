from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")


class UserAuthSchema(BaseModel):
    username: str
    password: str