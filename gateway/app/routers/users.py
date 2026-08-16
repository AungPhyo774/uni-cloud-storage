from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

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
    # 1. Validate role
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
    # 2. Validate class
    # -----------------------------------------------------

    allowed_classes = [
        "first_year",
        "second_year",
        "third_year",
        "fourth_year",
        "fifth_year"
    ]

    if data.class_year not in allowed_classes:

        raise HTTPException(
            status_code=400,
            detail="Invalid class year"
        )

    # -----------------------------------------------------
    # 3. Check duplicate email
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
    # 4. Create user
    # -----------------------------------------------------

    new_user = User(
        full_name=data.full_name,
        email=data.email,
        password_hash=hash_password(
            data.password
        ),
        role=data.role,
        class_year=data.class_year,
        is_active=True
    )

    try:

        db.add(new_user)

        db.commit()

        db.refresh(new_user)

    except IntegrityError as error:

        db.rollback()

        print(
            f"[CREATE USER ERROR] {error}"
        )

        raise HTTPException(
            status_code=400,
            detail=(
                "User could not be created. "
                "Check email or database constraints."
            )
        )

    return new_user