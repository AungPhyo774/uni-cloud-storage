from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.recovery_log import RecoveryLog
from app.models.user import User
from app.dependencies.auth import get_current_user


router = APIRouter(
    prefix="/recovery-logs",
    tags=["Recovery Monitoring"]
)