from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.v1 import (
    customer, product, review, seller, admin, login, cart, address, order,
    seller_management, esewa_router
)
from backend.database import Base, engine
from pathlib import Path
app = FastAPI()

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://unsight-unartificially-mozelle.ngrok-free.dev", 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,  
    allow_methods=["*"],
    allow_headers=["*"],
)
BASE_DIR = Path(__file__).resolve().parent         
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

Base.metadata.create_all(bind=engine)

app.include_router(login.router)
app.include_router(customer.router)
app.include_router(product.router)
app.include_router(address.router)
app.include_router(order.router)
app.include_router(review.router)
app.include_router(seller.router)
app.include_router(admin.router)
app.include_router(cart.router)
app.include_router(seller_management.router)
app.include_router(esewa_router.router)

@app.get("/")
def hello_world():
    return {"message": "hello this is online store"}
