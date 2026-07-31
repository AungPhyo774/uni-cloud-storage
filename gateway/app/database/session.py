import os

from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

#create_engine=FastAPI နဲ့ PostgreSQL ကြား Connection ကိုဖန်တီးတယ်။
engine = create_engine(
    DATABASE_URL,
    echo=True       #SQL query တွေကို ပြပေးတယ်။
)

#SessionLocal = Database ကို Insert,Update,Delete,Select လုပ်ဖို့ Session ထုတ်ပေးတယ်။

SessionLocal = sessionmaker(
    autoflush=False,
    autocommit=False,
    bind=engine
)



def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()