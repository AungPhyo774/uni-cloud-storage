from sqlalchemy import (
    Column,
    Integer,
    String
)

from app.database.base import Base


class ClassYear(Base):

    __tablename__ = "class_years"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    class_year = Column(
        String(20),
        unique=True,
        nullable=False
    )

    display_name = Column(
        String(100),
        nullable=False
    )