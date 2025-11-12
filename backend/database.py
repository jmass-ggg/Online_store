from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

import os

from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("Database is not set")

engine=create_engine(
                    DATABASE_URL,
                    pool_pre_ping=True,
                    pool_size=10,
                    echo=False,max_overflow=20,
                    pool_timeout=30,
                    pool_recycle=1800
                    )


SessionLocal=sessionmaker(autocommit=False,autoflush=False,bind=engine)
Base=declarative_base()

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()


