from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import require_role

from app.models.user import User
from app.models.class_year import ClassYear
from app.models.lecturer_teaching_class import (
    LecturerTeachingClass
)


router = APIRouter(
    prefix="/lecturers",
    tags=["Lecturer Classes"]
)


# =========================================================
# SCHEMA
# =========================================================

class LecturerClassesUpdate(BaseModel):
    class_years: list[str]


# =========================================================
# ALL AVAILABLE CLASSES
# =========================================================

@router.get("/classes")
def get_available_classes(
    current_user: User = Depends(
        require_role("lecturer")
    ),
    db: Session = Depends(get_db)
):
    classes = (
        db.query(ClassYear)
        .order_by(ClassYear.id.asc())
        .all()
    )

    return [
        {
            "id": item.id,
            "class_year": item.class_year,
            "display_name": item.display_name
        }
        for item in classes
    ]


# =========================================================
# CURRENT LECTURER CLASSES
# =========================================================

@router.get("/me/classes")
def get_my_teaching_classes(
    current_user: User = Depends(
        require_role("lecturer")
    ),
    db: Session = Depends(get_db)
):

    rows = (
        db.query(LecturerTeachingClass)
        .filter(
            LecturerTeachingClass.lecturer_id
            == current_user.id
        )
        .all()
    )

    classes = []

    for row in rows:

        class_record = (
            db.query(ClassYear)
            .filter(
                ClassYear.id == row.class_id
            )
            .first()
        )

        if class_record:

            classes.append(
                {
                    "id": class_record.id,
                    "class_year":
                        class_record.class_year,
                    "display_name":
                        class_record.display_name
                }
            )

    return {
        "lecturer_id":
            current_user.id,

        "lecturer_name":
            current_user.full_name,

        "classes":
            classes
    }


# =========================================================
# UPDATE CURRENT LECTURER CLASSES
# =========================================================

@router.put("/me/classes")
def update_my_teaching_classes(
    data: LecturerClassesUpdate,
    current_user: User = Depends(
        require_role("lecturer")
    ),
    db: Session = Depends(get_db)
):

    unique_classes = list(
        dict.fromkeys(
            data.class_years
        )
    )

    if not unique_classes:

        raise HTTPException(
            status_code=400,
            detail="Please select at least one class"
        )

    class_records = (
        db.query(ClassYear)
        .filter(
            ClassYear.class_year.in_(unique_classes)
        )
        .all()
    )

    if len(class_records) != len(unique_classes):

        found_classes = {
            item.class_year
            for item in class_records
        }
        invalid_classes = [
            item
            for item in unique_classes
            if item not in found_classes
        ]

        raise HTTPException(
            status_code=400,
            detail={
                "message": "One or more classes were not created by admin",
                "invalid_classes": invalid_classes
            }
        )

    try:

        db.query(
            LecturerTeachingClass
        ).filter(
            LecturerTeachingClass.lecturer_id
            == current_user.id
        ).delete(
            synchronize_session=False
        )

        for class_record in class_records:

            db.add(
                LecturerTeachingClass(
                    lecturer_id=current_user.id,
                    class_id=class_record.id
                )
            )

        db.commit()

    except Exception as error:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to update teaching classes: "
                f"{str(error)}"
            )
        )

    return {
        "message":
            "Teaching classes updated successfully",
        "classes":
            unique_classes
    }