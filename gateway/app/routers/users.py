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
from app.utils.password_generator import generate_password
from app.models.class_year import ClassYear
from app.models.lecturer_teaching_class import LecturerTeachingClass

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



@router.get("/admin/users")
def get_admin_users(
    current_user: User = Depends(
        require_role("admin")
    ),
    db: Session = Depends(get_db)
):

    users = (
        db.query(User)
        .order_by(User.id.desc())
        .all()
    )

    result = []

    for user in users:

        classes = []

        # =============================================
        # Lecturer classes
        # =============================================

        if user.role == "lecturer":

            teaching_rows = (
                db.query(
                    LecturerTeachingClass
                )
                .filter(
                    LecturerTeachingClass.lecturer_id
                    == user.id
                )
                .all()
            )

            for row in teaching_rows:

                class_record = (
                    db.query(ClassYear)
                    .filter(
                        ClassYear.id
                        == row.class_id
                    )
                    .first()
                )

                if class_record:

                    classes.append(
                        class_record.class_year
                    )

        result.append(
            {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "role": user.role,
                "class_year": user.class_year,
                "classes": classes,
                "is_active": bool(
                    user.is_active
                ),
                "created_at": user.created_at
            }
        )

    return result


# =========================================================
# ADMIN CREATE USER
# =========================================================

@router.post(
    "/admin/create-user"
)
def admin_create_user(
    data: AdminCreateUser,
    current_user: User = Depends(
        require_role("admin")
    ),
    db: Session = Depends(get_db)
):

    # =====================================================
    # 1. Validate role
    # =====================================================

    if data.role not in [
        "student",
        "lecturer"
    ]:

        raise HTTPException(
            status_code=400,
            detail="Role must be student or lecturer"
        )

    # =====================================================
    # 2. Student class validation
    # =====================================================

    allowed_classes = {
        "first_year",
        "second_year",
        "third_year",
        "fourth_year",
        "fifth_year"
    }

    if data.role == "student":

        if data.class_year not in allowed_classes:

            raise HTTPException(
                status_code=400,
                detail="Invalid student class"
            )

    # =====================================================
    # 3. Check duplicate email
    # =====================================================

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

    # =====================================================
    # 4. Generate 6-character password
    # =====================================================

    generated_password = (
        generate_password(6)
    )

    # =====================================================
    # 5. Create user
    # =====================================================

    new_user = User(
        full_name=data.full_name,
        email=data.email,
        password_hash=hash_password(
            generated_password
        ),
        role=data.role,
        class_year=(
            data.class_year
            if data.role == "student"
            else None
        ),
        is_active=True
    )

    try:

        db.add(new_user)

        db.flush()

        # =================================================
        # 6. Lecturer multiple classes
        # =================================================

        if data.role == "lecturer":

            if not data.classes:

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "At least one teaching "
                        "class is required"
                    )
                )

            for class_name in data.classes:

                class_record = (
                    db.query(ClassYear)
                    .filter(
                        ClassYear.class_year
                        == class_name
                    )
                    .first()
                )

                if class_record is None:

                    raise HTTPException(
                        status_code=400,
                        detail=(
                            f"Invalid class: "
                            f"{class_name}"
                        )
                    )

                teaching_class = (
                    LecturerTeachingClass(
                        lecturer_id=new_user.id,
                        class_id=class_record.id
                    )
                )

                db.add(teaching_class)

        db.commit()

        db.refresh(new_user)

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to create user: "
                f"{str(error)}"
            )
        )

    # =====================================================
    # 7. Return password ONLY in creation response
    # =====================================================

    return {
        "message": "User created successfully",

        "user": {
            "id": new_user.id,
            "full_name": new_user.full_name,
            "email": new_user.email,
            "role": new_user.role,
            "class_year": new_user.class_year,
            "is_active": new_user.is_active
        },

        "generated_password": generated_password
    }


    