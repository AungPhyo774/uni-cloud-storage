from fastapi import FastAPI

from app.database.base import Base
from app.database.session import engine

from app.routers import auth
from app.routers import users
from app.routers import documents

from app.models.user import User
from app.models.document import Document

from app.routers import health

import asyncio

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.services.recovery_service import (
    run_recovery_check
)

# # Create Database Tables
Base.metadata.create_all(bind=engine)

async def recovery_loop():

    while True:

        try:

            print(
                "[RECOVERY] Checking files..."
            )

            await run_recovery_check()

        except Exception as error:

            print(
                f"[RECOVERY ERROR] {error}"
            )

        await asyncio.sleep(30)


@asynccontextmanager
async def lifespan(app: FastAPI):

    recovery_task = asyncio.create_task(
        recovery_loop()
    )

    yield

    recovery_task.cancel()

app = FastAPI(
    title="Distributed Cloud Storage Gateway",
    lifespan=lifespan
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