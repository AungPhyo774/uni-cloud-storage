from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query
)

from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.recovery_log import RecoveryLog


router = APIRouter(
    prefix="/recovery",
    tags=["Recovery"]
)

def require_admin(
    current_user: User = Depends(
        get_current_user
    )
):

    if current_user.role != "admin":

        raise HTTPException(
            status_code=403,
            detail="Only admin can access recovery monitoring"
        )

    return current_user


@router.get("/logs")
def get_recovery_logs(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):

    logs = (
        db.query(RecoveryLog)
        .order_by(
            RecoveryLog.created_at.desc()
        )
        .all()
    )

    return [
        {
            "id": log.id,
            "document_id": log.document_id,
            "file_name": log.file_name,
            "source_node": log.source_node,
            "target_node": log.target_node,
            "status": log.status,
            "message": log.message,
            "created_at": log.created_at
        }
        for log in logs
    ]


@router.get("/logs/filter")
def get_recovery_logs_by_status(
    status: str | None = Query(
        default=None
    ),
    current_user: User = Depends(
        require_admin
    ),
    db: Session = Depends(get_db)
):

    query = (
        db.query(RecoveryLog)
    )

    if status:

        query = query.filter(
            RecoveryLog.status == status
        )

    logs = (
        query
        .order_by(
            RecoveryLog.created_at.desc()
        )
        .all()
    )

    return [
        {
            "id": log.id,
            "document_id": log.document_id,
            "file_name": log.file_name,
            "source_node": log.source_node,
            "target_node": log.target_node,
            "status": log.status,
            "message": log.message,
            "created_at": log.created_at
        }
        for log in logs
    ]


@router.get("/stats")
def get_recovery_stats(
    current_user: User = Depends(
        require_admin
    ),
    db: Session = Depends(get_db)
):

    total = (
        db.query(RecoveryLog)
        .count()
    )

    success = (
        db.query(RecoveryLog)
        .filter(
            RecoveryLog.status == "SUCCESS"
        )
        .count()
    )

    failed = (
        db.query(RecoveryLog)
        .filter(
            RecoveryLog.status == "FAILED"
        )
        .count()
    )
    checksum_mismatch = (
        db.query(RecoveryLog)
        .filter(
            RecoveryLog.status
            == "CHECKSUM_MISMATCH"
        )
        .count()
    )

    return {
        "total_recovery_attempts": total,
        "successful": success,
        "failed": failed,
        "checksum_mismatch": checksum_mismatch
    }


@router.get("/latest")
def get_latest_recovery(
    current_user: User = Depends(
        require_admin
    ),
    db: Session = Depends(get_db)
):

    log = (
        db.query(RecoveryLog)
        .order_by(
            RecoveryLog.created_at.desc()
        )
        .first()
    )

    if log is None:

        return {
            "message": "No recovery logs found"
        }

    return {
        "id": log.id,
        "document_id": log.document_id,
        "file_name": log.file_name,
        "source_node": log.source_node,
        "target_node": log.target_node,
        "status": log.status,
        "message": log.message,
        "created_at": log.created_at
    }


@router.get("/document/{document_id}")
def get_document_recovery_logs(
    document_id: int,
    current_user: User = Depends(
        require_admin
    ),
    db: Session = Depends(get_db)
):

    logs = (
        db.query(RecoveryLog)
        .filter(
            RecoveryLog.document_id == document_id
        )
        .order_by(
            RecoveryLog.created_at.desc()
        )
        .all()
    )

    return [
        {
            "id": log.id,
            "file_name": log.file_name,
            "source_node": log.source_node,
            "target_node": log.target_node,
            "status": log.status,
            "message": log.message,
            "created_at": log.created_at
        }
        for log in logs
    ]


@router.get("/node-summary")
def get_node_recovery_summary(
    current_user: User = Depends(
        require_admin
    ),
    db: Session = Depends(get_db)
):

    logs = (
        db.query(RecoveryLog)
        .filter(
            RecoveryLog.status == "SUCCESS"
        )
        .all()
    )

    summary = {}

    for log in logs:

        if not log.source_node or not log.target_node:
            continue

        key = (
            f"{log.source_node} -> "
            f"{log.target_node}"
        )

        if key not in summary:
            summary[key] = 0

        summary[key] += 1

    return summary