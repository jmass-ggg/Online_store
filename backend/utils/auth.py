
from fastapi.security import OAuth2PasswordBearer

access_schema = OAuth2PasswordBearer(tokenUrl="user/login")
refresh_schema = OAuth2PasswordBearer(tokenUrl="user/refresh")
