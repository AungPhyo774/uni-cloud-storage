from fastapi import APIRouter, Depends

from app.dependencies.auth import (
    get_current_user,
    require_role
)

from app.models.user import User
from app.schemas.user import UserResponse


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: User = Depends(get_current_user)
):
    return current_user


@router.get("/student-area")
def student_area(
    current_user: User = Depends(
        require_role("student")
    )
):
    return {
        "message": "Welcome student",
        "user": current_user.full_name,
        "role": current_user.role
    }

@router.get("/admin-area")
def admin_area(
    current_user: User = Depends(
        require_role("admin")
    )
):
    return {
        "message": "Welcome administrator",
        "user": current_user.full_name,
        "role": current_user.role
    }