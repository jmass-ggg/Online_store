from fastapi import FastAPI,Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.v1 import (
    customer, product, review, seller, admin, login, cart, address, order,
    seller_management, esewa_router,checkout
)
from contextlib import asynccontextmanager
from slowapi import Limiter,_rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from backend.database import Base, engine
from pathlib import Path
from redis import asyncio as redis
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache import FastAPICache
import time

@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_client = redis.from_url("redis://127.0.0.1:6379/0")
    FastAPICache.init(RedisBackend(redis_client), prefix="mystore-cache")
    yield
    await redis_client.close()

class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://0.0.0.0:5173",
    "http://frontend:5173",
    "http://localhost:5171",
    "https://unsight-unartificially-mozelle.ngrok-free.dev",
]
limiter=Limiter(key_func=get_remote_address)
app.state.limiter=limiter
app.add_exception_handler(RateLimitExceeded,_rate_limit_exceeded_handler)
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
app.include_router(checkout.router)
@app.get("/")
def hello_world():
    return {"message": "hello this is online store"}
@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start
    response.headers["X-Process-Time"] = f"{process_time:.6f}"
    return response