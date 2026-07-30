# from fastapi import Depends #FastAPI ကို Database Session ပေးပါလို့ ပြောတာ

# # FastAPI ကို Dependency Injection လုပ်ဖို့ Depends ကို သုံးတယ်။ "Dependency Injection" ဆိုတာ Function တစ်ခုကို အခြား Function တစ်ခုထဲမှာ Parameter အနေနဲ့ ထည့်သုံးနိုင်ဖို့ ဖြစ်ပါတယ်။ ဥပမာ Database Session ကို API Endpoint Function ထဲမှာ အသုံးပြုချင်ရင် Depends ကို သုံးပြီး get_db() function ကို parameter အနေနဲ့ ထည့်သုံးနိုင်ပါတယ်။ ဒီလိုသုံးရင် FastAPI က get_db() function ကို ခေါ်ပြီး Database Session ကို API Endpoint Function ထဲကို ပေးပါလိမ့်မယ်။ ဒီလိုသုံးရင် "Database Session ပေးပါ" လို့ ပြောတာပါ။

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.schemas.user import UserRegister
from app.schemas.token import Token
from app.services.user_service import authenticate_user
from app.utils.security import hash_password
from app.utils.jwt import create_access_token


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# =========================
# Register
# =========================

@router.post("/register")
def register(
    user: UserRegister,
    db: Session = Depends(get_db)
):
    hashed_password = hash_password(user.password)

    new_user = User(
        full_name=user.full_name,
        email=user.email,
        password_hash=hashed_password,
        role="student"
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully"
    }


# =========================
# Login
# =========================

@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    authenticated_user = authenticate_user(
        db,
        form_data.username,
        form_data.password
    )

    if not authenticated_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        data={
            "sub": str(authenticated_user.id),
            "email": authenticated_user.email,
            "role": authenticated_user.role
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }