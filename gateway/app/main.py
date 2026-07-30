from fastapi import FastAPI

from app.database.base import Base
from app.database.session import engine

from app.routers import auth
from app.routers import users


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Distributed Cloud Storage Gateway"
)


app.include_router(auth.router)
app.include_router(users.router)

# Create Database Tables
Base.metadata.create_all(bind=engine)


@app.get("/")
def home():
    return {
        "message": "Distributed Cloud Storage System API"
    }