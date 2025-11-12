from fastapi.security import OAuth2PasswordBearer

auth2_schema=OAuth2PasswordBearer(tokenUrl="/user/login")