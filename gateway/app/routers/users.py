# from fastapi import APIRouter, Depends

# from app.dependencies.auth import (
#     get_current_user,
#     require_role
# )

# from app.models.user import User
# from app.schemas.user import UserResponse


# router = APIRouter(
#     prefix="/users",
#     tags=["Users"]
# )


# @router.get("/me", response_model=UserResponse)
# def get_me(
#     current_user: User = Depends(get_current_user)
# ):
#     return current_user


# @router.get("/student-area")
# def student_area(
#     current_user: User = Depends(
#         require_role("student")
#     )
# ):
#     return {
#         "message": "Welcome student",
#         "user": current_user.full_name,
#         "role": current_user.role
#     }

# @router.get("/admin-area")
# def admin_area(
#     current_user: User = Depends(
#         require_role("admin")
#     )
# ):
#     return {
#         "message": "Welcome administrator",
#         "user": current_user.full_name,
#         "role": current_user.role
#     }




from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from app.database.session import get_db

from app.dependencies.auth import (
    get_current_user,
    require_role
)

from app.models.user import User

from app.schemas.user import (
    AdminCreateUser,
    UserResponse
)

from app.utils.security import hash_password


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


# =========================================================
# CURRENT USER
# =========================================================

@router.get(
    "/me",
    response_model=UserResponse
)
def get_me(
    current_user: User = Depends(
        get_current_user
    )
):

    return current_user


# =========================================================
# STUDENT AREA
# =========================================================

@router.get("/student-area")
def student_area(
    current_user: User = Depends(
        require_role("student")
    )
):

    return {
        "message": "Welcome student",
        "user": current_user.full_name,
        "role": current_user.role,
        "class_year": current_user.class_year
    }


# =========================================================
# ADMIN AREA
# =========================================================

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


# =========================================================
# ADMIN CREATE USER
# =========================================================

@router.post(
    "/admin/create-user",
    response_model=UserResponse
)
def admin_create_user(
    data: AdminCreateUser,
    current_user: User = Depends(
        require_role("admin")
    ),
    db: Session = Depends(get_db)
):

    # -----------------------------------------------------
    # Validate role
    # -----------------------------------------------------

    if data.role not in [
        "student",
        "lecturer"
    ]:

        raise HTTPException(
            status_code=400,
            detail=(
                "Role must be "
                "student or lecturer"
            )
        )

    # -----------------------------------------------------
    # Validate class year
    # -----------------------------------------------------

    if data.class_year not in [
        "first_year",
        "second_year",
        "third_year"
    ]:

        raise HTTPException(
            status_code=400,
            detail="Invalid class year"
        )

    # -----------------------------------------------------
    # Check duplicate email
    # -----------------------------------------------------

    existing_user = (
        db.query(User)
        .filter(
            User.email == data.email
        )
        .first()
    )

    if existing_user:

        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )

    # -----------------------------------------------------
    # Create user
    # -----------------------------------------------------

    new_user = User(
        full_name=data.full_name,
        email=data.email,
        password_hash=hash_password(
            data.password
        ),
        role=data.role,
        class_year=data.class_year
    )

    db.add(new_user)

    db.commit()

    db.refresh(new_user)

    return new_user