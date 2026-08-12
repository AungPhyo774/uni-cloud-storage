import hashlib
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

from app.services.storage_service import (
    check_node_health,
    check_file_on_node,
    recover_file_to_node
)

from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.services.storage_service import upload_to_storage
from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.document import Document

from app.utils.checksum import calculate_checksum

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
            User.role == "lecturer",
            User.class_year == current_user.class_year
        )
        .first()
    )


    if lecturer is None:
        raise HTTPException(
            status_code=403,
            detail=(
                "You can only upload documents "
                "to lecturers from your own class"
            )
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
    
    checksum = hashlib.sha256(
        file_content
        ).hexdigest()

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
            replica_node=replica_node,
            checksum=checksum
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
            "storage_node": new_document.storage_node,
            "replica_node": new_document.replica_node,
            "checksum": new_document.checksum
        }

    except Exception as e:

        raise HTTPException(
            status_code=503,
            detail=str(e)
        )

# ---------------------------------------------------------
# Get Lecturer List
# Students can use this list when uploading documents
# ---------------------------------------------------------

@router.get("/lecturers-list")
def get_lecturers(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    if current_user.role != "student":

        raise HTTPException(
            status_code=403,
            detail="Only students can access lecturer list"
        )

    lecturers = (
        db.query(User)
        .filter(
            User.role == "lecturer",
            User.class_year == current_user.class_year
        )
        .order_by(
            User.full_name
        )
        .all()
    )

    return [
        {
            "id": lecturer.id,
            "full_name": lecturer.full_name,
            "email": lecturer.email,
            "class_year": lecturer.class_year
        }
        for lecturer in lecturers
    ]

# ------Lecturer Documents List

@router.get("/lecturer-documents")
def get_lecturer_documents(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    if current_user.role != "student":

        raise HTTPException(
            status_code=403,
            detail=(
                "Only students can access "
                "lecturer documents"
            )
        )

    documents = (
        db.query(Document)
        .join(
            User,
            Document.owner_id == User.id
        )
        .filter(
            User.role == "lecturer",
            User.class_year == current_user.class_year
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
            "created_at": document.created_at,
            "lecturer": document.owner_id
        }
        for document in documents
    ]

#lecturer view student documents
@router.get("/student-documents")
def get_student_documents(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    if current_user.role != "lecturer":

        raise HTTPException(
            status_code=403,
            detail=(
                "Only lecturers can access "
                "student documents"
            )
        )

    documents = (
        db.query(Document)
        .join(
            User,
            Document.owner_id == User.id
        )
        .filter(
            User.role == "student",
            User.class_year == current_user.class_year,
            Document.lecturer_id == current_user.id
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
            "student_id": document.owner_id,
            "storage_node": document.storage_node,
            "created_at": document.created_at
        }
        for document in documents
    ]


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

# build Recovery Endpoint
@router.post("/recovery/{document_id}")
async def recover_document_endpoint(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # =====================================================
    # ONLY ADMIN CAN PERFORM RECOVERY
    # =====================================================

    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admin can perform document recovery"
        )

    # =====================================================
    # FIND DOCUMENT
    # =====================================================

    document = (
        db.query(Document)
        .filter(
            Document.id == document_id
        )
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    primary = document.storage_node
    replica = document.replica_node

    file_name = os.path.basename(
        document.file_path
    )

    # =====================================================
    # CHECK PRIMARY
    # =====================================================

    primary_online = await check_node_health(
        primary
    )

    # =====================================================
    # CHECK REPLICA
    # =====================================================

    replica_online = await check_node_health(
        replica
    )

    if (
        not primary_online
        and not replica_online
    ):
        raise HTTPException(
            status_code=503,
            detail="Both storage nodes are offline"
        )

    # =====================================================
    # PRIMARY ONLINE -> CHECK FILE
    # =====================================================

    primary_has_file = False

    if primary_online:

        primary_has_file = await check_file_on_node(
            primary,
            file_name
        )

    print(
        f"[RECOVERY] Primary: {primary}"
    )

    print(
        f"[RECOVERY] Primary online: "
        f"{primary_online}"
    )

    print(
        f"[RECOVERY] Primary file exists: "
        f"{primary_has_file}"
    )

    # =====================================================
    # PRIMARY FILE EXISTS
    # =====================================================

    if primary_has_file:

        return {
            "message": "No recovery needed",
            "document_id": document.id,
            "file_name": document.file_name,
            "primary": primary,
            "replica": replica
        }

    # =====================================================
    # REPLICA MUST BE ONLINE
    # =====================================================

    if not replica_online:

        raise HTTPException(
            status_code=503,
            detail="Replica node is offline"
        )

    # =====================================================
    # CHECK REPLICA FILE
    # =====================================================

    replica_has_file = await check_file_on_node(
        replica,
        file_name
    )

    print(
        f"[RECOVERY] Replica: "
        f"{replica}"
    )

    print(
        f"[RECOVERY] Replica online: "
        f"{replica_online}"
    )

    print(
        f"[RECOVERY] Replica file exists: "
        f"{replica_has_file}"
    )

    if not replica_has_file:

        raise HTTPException(
            status_code=404,
            detail="File does not exist on replica"
        )

    # =====================================================
    # RECOVER REPLICA -> PRIMARY
    # =====================================================

    success = await recover_file_to_node(
        source_node=replica,
        target_node=primary,
        file_name=file_name,
        content_type=document.content_type
    )

    if not success:

        raise HTTPException(
            status_code=500,
            detail="Document recovery failed"
        )

    return {
        "message": "Document recovered successfully",
        "document_id": document.id,
        "file_name": document.file_name,
        "recovered_from": replica,
        "recovered_to": primary
    }

# =========================================================
# DOWNLOAD DOCUMENT
# =========================================================
@router.get("/{document_id}/download")
async def download_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # =====================================================
    # 1. Find document
    # =====================================================

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

    # =====================================================
    # 2. Find document owner
    # =====================================================

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

    # =====================================================
    # 3. Permission
    # =====================================================

    allowed = False

    # Owner can download
    if document.owner_id == current_user.id:

        allowed = True

    # Student can download lecturer documents
    elif (
        current_user.role == "student"
        and owner.role == "lecturer"
        and owner.class_year
            == current_user.class_year
    ):
        allowed = True

    # Lecturer can download documents specifically
    # assigned to that lecturer
    elif (
        current_user.role == "lecturer"
        and owner.role == "student"
        and document.lecturer_id == current_user.id
        and owner.class_year
            == current_user.class_year
    ):
        allowed = True

# =====================================================
# 4. ADMIN
# =====================================================

    elif current_user.role == "admin":

        allowed = True

    if not allowed:

        raise HTTPException(
            status_code=403,
            detail="You do not have permission to download this document"
        )

    # =====================================================
    # 4. Get file name
    # =====================================================

    file_name = os.path.basename(
        document.file_path
    )

    # =====================================================
    # 5. Prepare Primary + Replica
    # =====================================================

    storage_nodes = []

    if document.storage_node:

        storage_nodes.append(
            document.storage_node
        )

    if (
        document.replica_node
        and document.replica_node
        != document.storage_node
    ):

        storage_nodes.append(
            document.replica_node
        )

    if not storage_nodes:

        raise HTTPException(
            status_code=500,
            detail="No storage node information available"
        )

    # =====================================================
    # 6. Try Primary first, then Replica
    # =====================================================

    async with httpx.AsyncClient(
        timeout=10.0
    ) as client:

        for storage_node in storage_nodes:

            try:

                response = await client.get(
                    f"{storage_node}/storage/download/{file_name}"
                )

                # -----------------------------------------
                # File found
                # -----------------------------------------

                if response.status_code == 200:

                    return StreamingResponse(
                        io.BytesIO(
                            response.content
                        ),
                        media_type=document.content_type,
                        headers={
                            "Content-Disposition": (
                                f'attachment; '
                                f'filename="{document.file_name}"'
                            )
                        }
                    )

                # -----------------------------------------
                # File does not exist on this node
                # -----------------------------------------

                if response.status_code == 404:

                    continue

            except httpx.RequestError:

                # Node unavailable
                # Try next node
                continue

    # =====================================================
    # 7. Both Primary and Replica failed
    # =====================================================

    raise HTTPException(
        status_code=503,
        detail="File is unavailable from all storage nodes"
    )


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
from sqlalchemy.exc import IntegrityError

# =========================================================
# DELETE DOCUMENT
# =========================================================
@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # =====================================================
    # 1. Find document
    # =====================================================

    document = (
        db.query(Document)
        .filter(
            Document.id == document_id
        )
        .first()
    )

    if document is None:

        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    # =====================================================
    # 2. Permission
    # =====================================================

    if document.owner_id != current_user.id:

        raise HTTPException(
            status_code=403,
            detail=(
                "You do not have permission "
                "to delete this document"
            )
        )

    # =====================================================
    # 3. Save metadata BEFORE deleting object
    # =====================================================

    file_name = os.path.basename(
        document.file_path
    )

    primary_node = document.storage_node
    replica_node = document.replica_node

    try:

        async with httpx.AsyncClient(
            timeout=10.0
        ) as client:

            # =================================================
            # 4. Delete Primary
            # =================================================

            if primary_node:

                try:

                    primary_response = await client.delete(
                        f"{primary_node}/storage/delete/{file_name}"
                    )

                except httpx.RequestError:

                    raise HTTPException(
                        status_code=503,
                        detail=(
                            "Primary storage node "
                            "is unavailable"
                        )
                    )

                if primary_response.status_code not in [
                    200,
                    404
                ]:

                    raise HTTPException(
                        status_code=500,
                        detail=(
                            "Failed to delete file "
                            "from primary node"
                        )
                    )

            # =================================================
            # 5. Delete Replica
            # =================================================

            if replica_node:

                try:

                    replica_response = await client.delete(
                        f"{replica_node}/storage/delete/{file_name}"
                    )

                except httpx.RequestError:

                    raise HTTPException(
                        status_code=503,
                        detail=(
                            "Replica storage node "
                            "is unavailable"
                        )
                    )

                if replica_response.status_code not in [
                    200,
                    404
                ]:

                    raise HTTPException(
                        status_code=500,
                        detail=(
                            "Failed to delete file "
                            "from replica node"
                        )
                    )

        # =====================================================
        # 6. Delete PostgreSQL document metadata
        # =====================================================

        db.delete(document)

        db.commit()

        # =====================================================
        # 7. Response
        # =====================================================

        return {
            "message": "Document deleted successfully",
            "document_id": document_id,
            "file_name": file_name,
            "primary_node": primary_node,
            "replica_node": replica_node
        }

    except HTTPException:
        raise

    except IntegrityError:

        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "Document cannot be deleted because "
                "related database records still reference it"
            )
        )

    except Exception as error:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(error)}"
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

    checksum = hashlib.sha256(
        file_content
    ).hexdigest()

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
            replica_node=replica_node,
            checksum=checksum
        )

        db.add(new_document)
        db.commit()
        db.refresh(new_document)

        return {
            "message": "Lecturer document uploaded successfully",
            "document_id": new_document.id,
            "file_name": new_document.file_name,
            "lecturer": current_user.full_name,
            "storage_node": new_document.storage_node,
            "replica_node": new_document.replica_node,
            "checksum": new_document.checksum
        }

    except httpx.RequestError:

        raise HTTPException(
            status_code=503,
            detail="Storage Node is unavailable"
        )

