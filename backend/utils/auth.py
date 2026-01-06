from fastapi.security import OAuth2PasswordBearer

# MUST match your real login endpoint path:
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login/login")