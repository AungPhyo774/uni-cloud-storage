from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from app.services.node_health_service import get_node_health
from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user import (
    UserResponse,
    AdminUpdateUser
)

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)


def require_admin(
    current_user: User = Depends(
        get_current_user
    )
):

    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admin can access this resource"
        )

    return current_user


@router.patch(
    "/users/{user_id}",
    response_model=UserResponse
)
def update_user(
    user_id: int,
    data: AdminUpdateUser,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):

    user = (
        db.query(User)
        .filter(
            User.id == user_id
        )
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Class validation
    if (
        data.class_year is not None
        and data.class_year not in [
            "first_year",
            "second_year",
            "third_year",
            "fourth_year",
            "fifth_year"
        ]
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid class year"
        )

    # Update class
    if data.class_year is not None:
        user.class_year = data.class_year

    # Update active status
    if data.is_active is not None:
        user.is_active = data.is_active

    db.commit()
    db.refresh(user)

    return user

# =========================================================
# GET ALL USERS
# =========================================================

@router.get(
    "/users",
    response_model=list[UserResponse]
)
def get_all_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):

    users = (
        db.query(User)
        .order_by(
            User.id
        )
        .all()
    )

    return users


@router.get("/classes/summary")
def get_class_summary(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):

    result = {}

    class_years = [
        "first_year",
        "second_year",
        "third_year",
        "fourth_year",
        "fifth_year"
    ]

    for year in class_years:

        student_count = (
            db.query(User)
            .filter(
                User.role == "student",
                User.class_year == year
            )
            .count()
        )

        lecturer_count = (
            db.query(User)
            .filter(
                User.role == "lecturer",
                User.class_year == year
            )
            .count()
        )

        result[year] = {
            "students": student_count,
            "lecturers": lecturer_count
        }

    return result


@router.get("/nodes/health")
async def get_nodes_health(
    current_user: User = Depends(require_admin)
):

    nodes = await get_node_health()

    return {
        "nodes": nodes
    }