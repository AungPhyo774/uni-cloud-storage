from sqlalchemy import (
    Column,
    ForeignKey,
    Integer
)

from app.database.base import Base


class DocumentClass(Base):

    __tablename__ = "document_classes"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    document_id = Column(
        Integer,
        ForeignKey("documents.id"),
        nullable=False
    )

    class_id = Column(
        Integer,
        ForeignKey("class_years.id"),
        nullable=False
    )