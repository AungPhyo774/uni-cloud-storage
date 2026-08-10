from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.recovery_log import RecoveryLog


router = APIRouter(
    prefix="/recovery",
    tags=["Recovery"]
)


@router.get("/logs")
def get_recovery_logs(
    current_user: User = Depends(get_current_user),
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