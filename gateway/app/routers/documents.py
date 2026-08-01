import os

import httpx

from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    HTTPException
)

from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.document import Document

router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


STORAGE_SERVICE_URL = os.getenv(
    "STORAGE_SERVICE_URL",
    "http://127.0.0.1:9000"
)


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    try:
        file_content = await file.read()

        files = {
            "file": (
                file.filename,
                file_content,
                file.content_type
            )
        }

        async with httpx.AsyncClient() as client:

            response = await client.post(
                f"{STORAGE_SERVICE_URL}/storage/upload",
                files=files
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail="Storage Service failed to store the file"
            )

        storage_result = response.json()

        # Save document metadata
        new_document = Document(
            owner_id=current_user.id,
            file_name=file.filename,
            file_path=storage_result["file_path"],
            file_size=len(file_content),
            content_type=file.content_type,
            storage_node="storage-1"
        )

        db.add(new_document)
        db.commit()
        db.refresh(new_document)

        return {
            "message": "File uploaded successfully",
            "document_id": new_document.id,
            "file_name": new_document.file_name,
            "file_size": new_document.file_size,
            "content_type": new_document.content_type,
            "storage_node": new_document.storage_node,
            "user": current_user.full_name
        }

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Storage Service is unavailable"
        )