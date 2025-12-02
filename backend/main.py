import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.api.v1 import customer,product,order,review,seller,admin
from backend.database import Base, engine

app = FastAPI()

origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


# Routers
app.include_router(customer.router)
app.include_router(product.router)
app.include_router(order.router)
app.include_router(review.router)
app.include_router(seller.router)
app.include_router(admin.router)
@app.get("/")
def hello_world():
    return {"message": "hello this is online store "}
