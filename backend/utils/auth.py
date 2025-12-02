from fastapi.security import OAuth2PasswordBearer

customer_schema = OAuth2PasswordBearer(tokenUrl="/user/login")

admin_schema = OAuth2PasswordBearer(tokenUrl="/admin/login")

seller_schema = OAuth2PasswordBearer(tokenUrl="/seller/login")

refresh_schema = OAuth2PasswordBearer(tokenUrl="/user/refresh")
