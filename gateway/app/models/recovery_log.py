from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime

from app.database.base import Base


class RecoveryLog(Base):

    __tablename__ = "recovery_logs"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    document_id = Column(
        Integer,
        ForeignKey(
            "documents.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    file_name = Column(
        String,
        nullable=False
    )

    source_node = Column(
        String,
        nullable=True
    )

    target_node = Column(
        String,
        nullable=True
    )

    status = Column(
        String,
        nullable=False
    )

    message = Column(
        String,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )