import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# get the url form .env file or use a fallback for local testing 
SQLALCHEMY_DATABASE_URL= os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@db:5432/alemenodb"
)

# create the enginee
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=10,
    max_overflow=20,
)

# create a SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# the base class 
Base = declarative_base()

# a dependecny fun in fastAPI we will use to grab databse connection
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()