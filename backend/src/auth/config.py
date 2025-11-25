from passlib.context import CryptContext

JWT_SECRET_KEY = "1892dhianiandowqd0n"
TOKEN_EXPIRE_MINUTES = 30
PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")