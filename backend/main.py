from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.v1 import customer, product, review, seller, admin, login,cart,address,order,seller_management
from backend.database import Base, engine

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "/home/james/james/project/Online_store/backend/uploads"
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

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
@app.get("/")
def hello_world():
    return {"message": "hello this is online store"}
