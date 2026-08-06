from fastapi import FastAPI

from app.database.base import Base
from app.database.session import engine

from app.routers import auth
from app.routers import users
from app.routers import documents

from app.models.user import User
from app.models.document import Document

from app.routers import health

# # Create Database Tables
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Distributed Cloud Storage Gateway"
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(documents.router)


@app.get("/")
def home():
    return {
        "message": "Distributed Cloud Storage System API"
    }