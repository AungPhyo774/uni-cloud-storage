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
@router.post("/upload-to-lecturer/{lecturer_id}")
async def upload_document(
    lecturer_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # -------------------------------------------------
    # 1. Only students can upload documents to lecturers
    # -------------------------------------------------

    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Only students can upload documents to lecturers"
        )

    # -------------------------------------------------
    # 2. Find selected lecturer
    # -------------------------------------------------

    lecturer = (
        db.query(User)
        .filter(
            User.id == lecturer_id,
            User.role == "lecturer"
        )
        .first()
    )

    if lecturer is None:
        raise HTTPException(
            status_code=404,
            detail="Lecturer not found"
        )

    # -------------------------------------------------
    # 3. Read uploaded file
    # -------------------------------------------------

    file_content = await file.read()

    if not file_content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty"
        )

    try:

        # -------------------------------------------------
        # 4. Upload to Storage Node
        #
        # Round Robin:
        # Node 1 → Node 2 → Node 3 → Node 1
        # -------------------------------------------------

        storage_result = await upload_to_storage(
            file_content,
            file.filename,
            file.content_type
        )

        # -------------------------------------------------
        # 5. Get selected storage node
        # -------------------------------------------------

        storage_node = storage_result["storage_node"]

        # -------------------------------------------------
        # 6. Get storage response
        # -------------------------------------------------

        node_response = storage_result["response"]

        replica_node = storage_result["replica_node"]

        file_path = node_response["file_path"]

        # -------------------------------------------------
        # 7. Save metadata
        # -------------------------------------------------

        new_document = Document(
            owner_id=current_user.id,
            lecturer_id=lecturer_id,
            file_name=file.filename,
            file_path=file_path,
            file_size=len(file_content),
            content_type=file.content_type,
            storage_node=storage_node,
            replica_node=replica_node
        )

        db.add(new_document)
        db.commit()
        db.refresh(new_document)

        # -------------------------------------------------
        # 8. Response
        # -------------------------------------------------

        return {
            "message": "File uploaded successfully",
            "document_id": new_document.id,
            "file_name": new_document.file_name,
            "student": current_user.full_name,
            "lecturer": lecturer.full_name,
            "storage_node": new_document.storage_node
        }

    except httpx.RequestError:

        raise HTTPException(
            status_code=503,
            detail="Storage Node is unavailable"
        )

# ---------------------------------------------------------
# Get Lecturer List
# Students can use this list when uploading documents
# ---------------------------------------------------------

@router.get("/lecturers-list")
def get_lecturers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # -----------------------------------------------------
    # 1. Only students can access lecturer list
    # -----------------------------------------------------

    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Only students can access lecturer list"
        )

    # -----------------------------------------------------
    # 2. Get all lecturers
    # -----------------------------------------------------

    lecturers = (
        db.query(User)
        .filter(
            User.role == "lecturer"
        )
        .all()
    )
    return [
        {
            "id": lecturer.id,
            "full_name": lecturer.full_name,
            "email": lecturer.email
        }
        for lecturer in lecturers
    ]
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
    # 1. Find document
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
    # 2. Find owner
    # -------------------------------------------------

    owner = (
        db.query(User)
        .filter(User.id == document.owner_id)
        .first()
    )

    if owner is None:
        raise HTTPException(
            status_code=404,
            detail="Document owner not found"
        )

    # -------------------------------------------------
    # 3. Permission
    # -------------------------------------------------

    allowed = False

    # Owner can download
    if document.owner_id == current_user.id:
        allowed = True

    # Student can download lecturer documents
    elif (
        current_user.role == "student"
        and owner.role == "lecturer"
    ):
        allowed = True

    # Lecturer can download document shared with them
    elif (
        current_user.role == "lecturer"
        and document.lecturer_id == current_user.id
    ):
        allowed = True

    if not allowed:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to download this document"
        )

    # -------------------------------------------------
    # 4. File name
    # -------------------------------------------------

    file_name = os.path.basename(
        document.file_path
    )

    # -------------------------------------------------
    # 5. Primary + Replica
    # -------------------------------------------------

    primary_node = document.storage_node
    replica_node = document.replica_node

    nodes_to_try = [
        primary_node,
        replica_node
    ]

    # -------------------------------------------------
    # 6. Try Primary first
    #    If failed → try Replica
    # -------------------------------------------------

    async with httpx.AsyncClient(timeout=10.0) as client:

        for storage_node in nodes_to_try:

            if not storage_node:
                continue

            try:

                response = await client.get(
                    f"{storage_node}/storage/download/{file_name}"
                )

                # File successfully downloaded
                if response.status_code == 200:

                    return StreamingResponse(
                        io.BytesIO(response.content),
                        media_type=document.content_type,
                        headers={
                            "Content-Disposition": (
                                f'attachment; '
                                f'filename="{document.file_name}"'
                            )
                        }
                    )

                # Try next node
                if response.status_code in [404, 500, 502, 503]:
                    continue

            except httpx.RequestError:

                # Node unavailable
                continue

    # -------------------------------------------------
    # 7. Both nodes failed
    # -------------------------------------------------

    raise HTTPException(
        status_code=503,
        detail="Document is unavailable. Both storage nodes failed."
    )
  
# =========================================================
# LIST MY DOCUMENTS
# =========================================================

@router.get("/my-all-documents")
def get_my_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    documents = (
        db.query(Document)
        .filter(
            Document.owner_id == current_user.id
        )
        .order_by(
            Document.created_at.desc()
        )
        .all()
    )

    return [
        {
            "id": document.id,
            "file_name": document.file_name,
            "file_size": document.file_size,
            "content_type": document.content_type,
            "storage_node": document.storage_node,
            "created_at": document.created_at
        }
        for document in documents
    ]

# ------Lecturer Documents List

@router.get("/lecturer-documents")
def get_lecturer_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Only students can access lecturer documents"
        )

    documents = (
        db.query(Document)
        .join(User, Document.owner_id == User.id)
        .filter(User.role == "lecturer")
        .order_by(Document.created_at.desc())
        .all()
    )

    return [
        {
            "id": document.id,
            "file_name": document.file_name,
            "file_size": document.file_size,
            "content_type": document.content_type,
            "storage_node": document.storage_node,
            "created_at": document.created_at,
            "lecturer": document.owner_id
        }
        for document in documents
    ]

# =========================================================
# GET DOCUMENT DETAIL
# =========================================================

@router.get("/{document_id}")
def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.owner_id == current_user.id
        )
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    return {
        "id": document.id,
        "file_name": document.file_name,
        "file_size": document.file_size,
        "content_type": document.content_type,
        "storage_node": document.storage_node,
        "created_at": document.created_at
    }

# =========================================================
# DELETE DOCUMENT
# =========================================================

@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # 1. Find document
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

    # 2. Check ownership
    if document.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to delete this document"
        )

    # Save values before deleting database object
    file_name_from_db = document.file_name
    file_name = os.path.basename(document.file_path)
    storage_node = document.storage_node

    try:

        # 3. Delete physical file
        async with httpx.AsyncClient() as client:

            response = await client.delete(
                f"{storage_node}/storage/delete/{file_name}"
            )

        # 4. Storage node error
        if response.status_code not in [200, 404]:
            raise HTTPException(
                status_code=500,
                detail="Storage Node failed to delete file"
            )

        # 5. Delete PostgreSQL metadata
        db.delete(document)

        # 6. Commit
        db.commit()

        return {
            "message": "Document deleted successfully",
            "document_id": document_id,
            "file_name": file_name_from_db,
            "storage_node": storage_node
        }

    except httpx.RequestError:

        db.rollback()

        raise HTTPException(
            status_code=503,
            detail="Storage Node is unavailable"
        )

#lecturer upload document
@router.post("/lecturer/upload")
async def lecturer_upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # -------------------------------------------------
    # 1. Only lecturers can use this endpoint
    # -------------------------------------------------

    if current_user.role != "lecturer":
        raise HTTPException(
            status_code=403,
            detail="Only lecturers can upload documents"
        )

    # -------------------------------------------------
    # 2. Read file
    # -------------------------------------------------

    file_content = await file.read()

    if not file_content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty"
        )

    try:

        # -------------------------------------------------
        # 3. Send to distributed storage
        #
        # Node 1 → Node 2 → Node 3 → Node 1
        # -------------------------------------------------

        storage_result = await upload_to_storage(
            file_content,
            file.filename,
            file.content_type
        )

        # -------------------------------------------------
        # 4. Get selected Storage Node
        # -------------------------------------------------

        storage_node = storage_result["storage_node"]

        replica_node = storage_result["replica_node"]
        
        node_response = storage_result["response"]

        file_path = node_response["file_path"]

        # -------------------------------------------------
        # 5. Save metadata
        #
        # Lecturer is the owner.
        # Students will be allowed to download this
        # document.
        # -------------------------------------------------

        new_document = Document(
            owner_id=current_user.id,
            lecturer_id=current_user.id,
            file_name=file.filename,
            file_path=file_path,
            file_size=len(file_content),
            content_type=file.content_type,
            storage_node=storage_node,
            replica_node=replica_node
        )

        db.add(new_document)
        db.commit()
        db.refresh(new_document)

        return {
            "message": "Lecturer document uploaded successfully",
            "document_id": new_document.id,
            "file_name": new_document.file_name,
            "lecturer": current_user.full_name,
            "storage_node": new_document.storage_node
        }

    except httpx.RequestError:

        raise HTTPException(
            status_code=503,
            detail="Storage Node is unavailable"
        )
