# from fastapi import APIRouter, Depends, HTTPException
# from fastapi.security import OAuth2PasswordRequestForm
# from sqlalchemy.orm import Session

# from app.database.session import get_db
# from app.models.user import User
# from app.schemas.user import UserRegister
# from app.schemas.token import Token
# from app.services.user_service import authenticate_user
# from app.utils.security import hash_password
# from app.utils.jwt import create_access_token


# router = APIRouter(
#     prefix="/auth",
#     tags=["Authentication"]
# )


# # =========================
# # Register
# # =========================

# # @router.post("/register")
# # def register(
# #     user: UserRegister,
# #     db: Session = Depends(get_db)
# # ):
# #     hashed_password = hash_password(user.password)

# #     new_user = User(
# #         full_name=user.full_name,
# #         email=user.email,
# #         password_hash=hashed_password,
# #         role="student"
# #     )

# #     db.add(new_user)
# #     db.commit()
# #     db.refresh(new_user)

# #     return {
# #         "message": "User registered successfully"
# #     }

# @router.post("/register")
# def register():

#     raise HTTPException(
#         status_code=403,
#         detail="Public registration is disabled"
#     )

# # =========================
# # Login
# # =========================

# @router.post("/login", response_model=Token)
# def login(
#     form_data: OAuth2PasswordRequestForm = Depends(),
#     db: Session = Depends(get_db)
# ):
#     authenticated_user = authenticate_user(
#         db,
#         form_data.username,
#         form_data.password
#     )

#     if not authenticated_user:
#         raise HTTPException(
#             status_code=401,
#             detail="Invalid email or password"
#         )

#     access_token = create_access_token(
#         data={
#             "sub": str(authenticated_user.id),
#             "email": authenticated_user.email,
#             "role": authenticated_user.role
#         }
#     )

#     return {
#         "access_token": access_token,
#         "token_type": "bearer"
#     }


from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.schemas.token import Token
from app.services.user_service import authenticate_user
from app.utils.jwt import create_access_token


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# =========================================================
# FIXED ADMIN CREDENTIALS
# Development / University Project Demo Only
# =========================================================

ADMIN_EMAIL = "admin@gmail.com"
ADMIN_PASSWORD = "admin123"


# =========================================================
# LOGIN
# =========================================================

@router.post(
    "/login",
    response_model=Token
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):

    email = form_data.username
    password = form_data.password

    # =====================================================
    # 1. CHECK FIXED ADMIN LOGIN
    # =====================================================

    if (
        email == ADMIN_EMAIL
        and password == ADMIN_PASSWORD
    ):

        access_token = create_access_token(
            data={
                "sub": "admin",
                "email": ADMIN_EMAIL,
                "role": "admin"
            }
        )

        return {
            "access_token": access_token,
            "token_type": "bearer"
        }

    # =====================================================
    # 2. CHECK NORMAL USER
    # Student / Lecturer
    # =====================================================

    authenticated_user = authenticate_user(
        db,
        email,
        password
    )

    if not authenticated_user:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # =====================================================
    # 3. CREATE JWT
    # =====================================================

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


# =========================================================
# PUBLIC REGISTER
# DISABLED
# =========================================================

@router.post("/register")
def register_disabled():

    raise HTTPException(
        status_code=403,
        detail=(
            "Public registration is disabled. "
            "Only admin can create users."
        )
    )