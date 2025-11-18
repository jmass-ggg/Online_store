from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime
from backend.database import get_db
from backend.models.seller import Seller
from backend.models.role import Roles
from backend.schemas.customer import (
   
)
from backend.utils.jwt import create_token, verify_token
from backend.utils.hashed import hashed_password, verify_password
from backend.core.permission import check_permission
from backend.core.error_handler import error_handler