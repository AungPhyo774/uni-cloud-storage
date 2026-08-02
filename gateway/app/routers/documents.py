import io
import os

import httpx

from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    HTTPException
)

from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.services.storage_service import upload_to_storage
from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.document import Document


router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


# =========================================================
# UPLOAD DOCUMENT
# =========================================================

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    try:

        # -------------------------------------------------
        # 1. Read uploaded file
        # -------------------------------------------------

        file_content = await file.read()

        if not file_content:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty"
            )

        # -------------------------------------------------
        # 2. Upload to Storage Node
        #
        # storage_service.py handles Round Robin:
        #
        # Node 1 → Node 2 → Node 3 → Node 1
        # -------------------------------------------------

        storage_result = await upload_to_storage(
            file_content,
            file.filename,
            file.content_type
        )

        # -------------------------------------------------
        # 3. Get selected Storage Node
        # -------------------------------------------------

        storage_node = storage_result["storage_node"]

        # -------------------------------------------------
        # 4. Get Storage Node response
        # -------------------------------------------------

        node_response = storage_result["response"]

        # -------------------------------------------------
        # 5. Get stored file path
        # -------------------------------------------------

        file_path = node_response["file_path"]

        # -------------------------------------------------
        # 6. Save metadata to PostgreSQL
        # -------------------------------------------------

        new_document = Document(
            owner_id=current_user.id,
            file_name=file.filename,
            file_path=file_path,
            file_size=len(file_content),
            content_type=file.content_type,
            storage_node=storage_node
        )

        db.add(new_document)

        db.commit()

        db.refresh(new_document)

        # -------------------------------------------------
        # 7. Return response
        # -------------------------------------------------

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
            detail="Storage Node is unavailable"
        )


# =========================================================
# DOWNLOAD DOCUMENT
# =========================================================

@router.get("/{document_id}/download")
async def download_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # -------------------------------------------------
    # 1. Find document in PostgreSQL
    # -------------------------------------------------

    document = (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )

    if document is None:

        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    # -------------------------------------------------
    # 2. Check ownership
    # -------------------------------------------------

    if document.owner_id != current_user.id:

        raise HTTPException(
            status_code=403,
            detail="You do not have permission to download this document"
        )

    # -------------------------------------------------
    # 3. Get file name
    # -------------------------------------------------

    file_name = os.path.basename(
        document.file_path
    )

    # -------------------------------------------------
    # 4. Get the Storage Node from Database
    #
    # Example:
    #
    # Node 1 → http://127.0.0.1:9001
    # Node 2 → http://127.0.0.1:9002
    # Node 3 → http://127.0.0.1:9003
    #
    # This is the important part.
    # -------------------------------------------------

    storage_node = document.storage_node

    try:

        # -------------------------------------------------
        # 5. Request file from the correct Storage Node
        # -------------------------------------------------

        async with httpx.AsyncClient() as client:

            response = await client.get(
                f"{storage_node}/storage/download/{file_name}"
            )

        # -------------------------------------------------
        # 6. File not found
        # -------------------------------------------------

        if response.status_code == 404:

            raise HTTPException(
                status_code=404,
                detail="File not found in storage"
            )

        # -------------------------------------------------
        # 7. Storage Node error
        # -------------------------------------------------

        if response.status_code != 200:

            raise HTTPException(
                status_code=500,
                detail="Storage Node failed to download the file"
            )

        # -------------------------------------------------
        # 8. Return file to user
        # -------------------------------------------------

        return StreamingResponse(
            io.BytesIO(response.content),
            media_type=document.content_type,
            headers={
                "Content-Disposition": (
                    f'attachment; filename="{document.file_name}"'
                )
            }
        )

    except httpx.RequestError:

        raise HTTPException(
            status_code=503,
            detail="Storage Node is unavailable"
        )