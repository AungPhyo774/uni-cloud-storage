from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer
)

from sqlalchemy.sql import func

from app.database.base import Base


class LecturerTeachingClass(Base):

    __tablename__ = "lecturer_teaching_classes"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    lecturer_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    class_id = Column(
        Integer,
        ForeignKey("class_years.id"),
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )