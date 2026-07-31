from fastapi import APIRouter, Depends, UploadFile, File

from app.dependencies.auth import get_current_user
from app.models.user import User


router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


@router.post("/upload")
def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    return {
        "message": "File received successfully",
        "file_name": file.filename,
        "content_type": file.content_type,
        "user": current_user.full_name
    }