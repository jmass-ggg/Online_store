from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login/")

refresh_schema = OAuth2PasswordBearer(tokenUrl="/user/refresh")
