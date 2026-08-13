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
from app.models.document import Document

from app.services.node_health_service import (
    check_node_health
)
from app.services.recovery_service import (
    get_node_checksum
)

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


@router.get("/replication/status")
async def get_replication_status(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):

    documents = (
        db.query(Document)
        .order_by(
            Document.created_at.desc()
        )
        .all()
    )

    results = []

    for document in documents:

        file_name = document.file_name

        primary = document.storage_node
        replica = document.replica_node

        expected_checksum = document.checksum

        # -------------------------------------------------
        # Check Primary
        # -------------------------------------------------

        primary_checksum = None

        if primary:

            primary_checksum = await get_node_checksum(
                primary,
                file_name
            )

        # -------------------------------------------------
        # Check Replica
        # -------------------------------------------------

        replica_checksum = None

        if replica:

            replica_checksum = await get_node_checksum(
                replica,
                file_name
            )

        # -------------------------------------------------
        # Determine status
        # -------------------------------------------------

        if (
            primary_checksum is not None
            and replica_checksum is not None
            and expected_checksum is not None
            and primary_checksum == expected_checksum
            and replica_checksum == expected_checksum
        ):

            status = "HEALTHY"

        elif primary_checksum is None:

            status = "PRIMARY_MISSING"

        elif replica_checksum is None:

            status = "REPLICA_MISSING"

        elif (
            expected_checksum
            and (
                primary_checksum != expected_checksum
                or replica_checksum != expected_checksum
            )
        ):

            status = "CHECKSUM_MISMATCH"

        else:

            status = "UNKNOWN"

        results.append(
            {
                "id": document.id,
                "file_name": file_name,
                "primary_node": primary,
                "replica_node": replica,
                "expected_checksum": expected_checksum,
                "primary_checksum": primary_checksum,
                "replica_checksum": replica_checksum,
                "status": status
            }
        )

    return {
        "documents": results
    }