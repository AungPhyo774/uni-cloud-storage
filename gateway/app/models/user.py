from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.sql import func

from app.database.base import Base


class User(Base):  # user Table ကို ကိုယ်စားပြုတယ်။
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    full_name = Column(String(100), nullable=False)

    email = Column(String(100), unique=True, nullable=False)

    password_hash = Column(String, nullable=False)

    role = Column(String(20), default="student")

    class_year = Column(String(20),nullable=True)
    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )