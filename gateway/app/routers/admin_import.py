from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile
)

from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import require_role
from app.models.user import User

from app.services.excel_service import (
    read_student_excel,
    read_lecturer_excel
)

from app.utils.password_generator import (
    generate_password
)

from app.utils.security import hash_password
from app.models.class_year import ClassYear

from app.models.lecturer_teaching_class import (
    LecturerTeachingClass
)

router = APIRouter(
    prefix="/admin/import",
    tags=["Admin Import"]
)


ALLOWED_CLASS_YEARS = {
    "first_year",
    "second_year",
    "third_year",
    "fourth_year",
    "fifth_year"
}


@router.post("/students")
async def import_students(
    file: UploadFile = File(...),
    current_user: User = Depends(
        require_role("admin")
    ),
    db: Session = Depends(get_db)
):

    # =====================================================
    # 1. File validation
    # =====================================================

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="Please select an Excel file"
        )

    if not file.filename.lower().endswith(
        ".xlsx"
    ):

        raise HTTPException(
            status_code=400,
            detail="Only .xlsx files are allowed"
        )

    # =====================================================
    # 2. Read Excel
    # =====================================================

    file_content = await file.read()

    if not file_content:

        raise HTTPException(
            status_code=400,
            detail="Excel file is empty"
        )

    try:

        rows = read_student_excel(
            file_content
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    # =====================================================
    # 3. Import result
    # =====================================================

    created_users = []
    skipped_users = []

    # =====================================================
    # 4. Process every row
    # =====================================================

    for row in rows:

        row_number = row["row_number"]

        full_name = row["full_name"]
        email = row["email"]
        class_year = row["class_year"]

        # ---------------------------------------------
        # Validate name
        # ---------------------------------------------

        if not full_name:

            skipped_users.append(
                {
                    "row": row_number,
                    "email": email,
                    "reason": "Full name is required"
                }
            )

            continue

        # ---------------------------------------------
        # Validate email
        # ---------------------------------------------

        if not email or "@" not in email:

            skipped_users.append(
                {
                    "row": row_number,
                    "email": email,
                    "reason": "Invalid email"
                }
            )

            continue

        # ---------------------------------------------
        # Validate class
        # ---------------------------------------------

        if class_year not in ALLOWED_CLASS_YEARS:

            skipped_users.append(
                {
                    "row": row_number,
                    "email": email,
                    "reason": (
                        f"Invalid student class: "
                        f"{class_year}. "
                        "A student can belong to only one class."
                    )
                }
            )
            continue

        # ---------------------------------------------
        # Check duplicate email
        # ---------------------------------------------

        existing_user = (
            db.query(User)
            .filter(
                User.email == email
            )
            .first()
        )

        if existing_user:

            skipped_users.append(
                {
                    "row": row_number,
                    "email": email,
                    "reason": "Email already exists"
                }
            )

            continue

        # ---------------------------------------------
        # Generate password
        # ---------------------------------------------

        generated_password = (
            generate_password(6)
        )

        # ---------------------------------------------
        # Create user
        # ---------------------------------------------

        new_user = User(
            full_name=full_name,
            email=email,
            password_hash=hash_password(
                generated_password
            ),
            role="student",
            class_year=class_year,
            is_active=True
        )

        db.add(new_user)

        db.flush()

        # ---------------------------------------------
        # Keep generated password for admin result
        # ---------------------------------------------

        created_users.append(
            {
                "id": new_user.id,
                "full_name": new_user.full_name,
                "email": new_user.email,
                "role": new_user.role,
                "class_year": new_user.class_year,
                "password": generated_password
            }
        )

    # =====================================================
    # 5. Commit
    # =====================================================

    try:

        db.commit()

    except Exception as error:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to import students: "
                f"{str(error)}"
            )
        )

    # =====================================================
    # 6. Return result
    # =====================================================

    return {
        "message": "Student import completed",
        "total_rows": len(rows),
        "created_count": len(
            created_users
        ),
        "skipped_count": len(
            skipped_users
        ),
        "created_users": created_users,
        "skipped_users": skipped_users
    }


@router.post("/lecturers")
async def import_lecturers(
    file: UploadFile = File(...),
    current_user: User = Depends(
        require_role("admin")
    ),
    db: Session = Depends(get_db)
):

    # =====================================================
    # 1. Validate file
    # =====================================================

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="Please select an Excel file"
        )

    if not file.filename.lower().endswith(
        ".xlsx"
    ):

        raise HTTPException(
            status_code=400,
            detail="Only .xlsx files are allowed"
        )

    # =====================================================
    # 2. Read file
    # =====================================================

    file_content = await file.read()

    if not file_content:

        raise HTTPException(
            status_code=400,
            detail="Excel file is empty"
        )

    try:

        rows = read_lecturer_excel(
            file_content
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    # =====================================================
    # 3. Result containers
    # =====================================================

    created_lecturers = []
    skipped_lecturers = []

    # =====================================================
    # 4. Process rows
    # =====================================================

    for row in rows:

        row_number = row["row_number"]

        full_name = row["full_name"]

        email = row["email"]

        classes_text = row["classes"]

        # ---------------------------------------------
        # Validate name
        # ---------------------------------------------

        if not full_name:

            skipped_lecturers.append(
                {
                    "row": row_number,
                    "email": email,
                    "reason": "Full name is required"
                }
            )

            continue

        # ---------------------------------------------
        # Validate email
        # ---------------------------------------------

        if not email or "@" not in email:

            skipped_lecturers.append(
                {
                    "row": row_number,
                    "email": email,
                    "reason": "Invalid email"
                }
            )

            continue

        # ---------------------------------------------
        # Check duplicate email
        # ---------------------------------------------

        existing_user = (
            db.query(User)
            .filter(
                User.email == email
            )
            .first()
        )

        if existing_user:

            skipped_lecturers.append(
                {
                    "row": row_number,
                    "email": email,
                    "reason": "Email already exists"
                }
            )

            continue

        # ---------------------------------------------
        # Parse classes
        # ---------------------------------------------

        class_names = [
            item.strip()
            for item in classes_text.split(",")
            if item.strip()
        ]

        if not class_names:

            skipped_lecturers.append(
                {
                    "row": row_number,
                    "email": email,
                    "reason": "No teaching class specified"
                }
            )

            continue

        # ---------------------------------------------
        # Validate classes
        # ---------------------------------------------

        class_records = []

        invalid_class = None

        for class_name in class_names:

            class_record = (
                db.query(ClassYear)
                .filter(
                    ClassYear.class_year
                    == class_name
                )
                .first()
            )

            if class_record is None:

                invalid_class = class_name

                break

            class_records.append(
                class_record
            )

        if invalid_class:

            skipped_lecturers.append(
                {
                    "row": row_number,
                    "email": email,
                    "reason": (
                        "Invalid class: "
                        f"{invalid_class}"
                    )
                }
            )

            continue

        # ---------------------------------------------
        # Generate password
        # ---------------------------------------------

        generated_password = (
            generate_password(6)
        )

        # ---------------------------------------------
        # Create lecturer
        # ---------------------------------------------

        new_lecturer = User(
            full_name=full_name,
            email=email,
            password_hash=hash_password(
                generated_password
            ),
            role="lecturer",
            class_year=None,
            is_active=True
        )

        db.add(new_lecturer)

        db.flush()

        # ---------------------------------------------
        # Assign teaching classes
        # ---------------------------------------------

        assigned_classes = []

        for class_record in class_records:

            teaching_class = (
                LecturerTeachingClass(
                    lecturer_id=new_lecturer.id,
                    class_id=class_record.id
                )
            )

            db.add(teaching_class)

            assigned_classes.append(
                class_record.class_year
            )

        # ---------------------------------------------
        # Result
        # ---------------------------------------------

        created_lecturers.append(
            {
                "id": new_lecturer.id,
                "full_name": new_lecturer.full_name,
                "email": new_lecturer.email,
                "role": new_lecturer.role,
                "classes": assigned_classes,
                "password": generated_password
            }
        )

    # =====================================================
    # 5. Commit
    # =====================================================

    try:

        db.commit()

    except Exception as error:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to import lecturers: "
                f"{str(error)}"
            )
        )

    # =====================================================
    # 6. Response
    # =====================================================

    return {
        "message": "Lecturer import completed",

        "total_rows": len(rows),

        "created_count": len(
            created_lecturers
        ),

        "skipped_count": len(
            skipped_lecturers
        ),

        "created_lecturers":
            created_lecturers,

        "skipped_lecturers":
            skipped_lecturers
    }