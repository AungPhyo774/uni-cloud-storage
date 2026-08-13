# from fastapi import Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordBearer
# from jose import JWTError, jwt
# from sqlalchemy.orm import Session

# from app.database.session import get_db
# from app.models.user import User
# from app.utils.jwt import SECRET_KEY, ALGORITHM


# oauth2_scheme = OAuth2PasswordBearer(
#     tokenUrl="/auth/login"
# )


# # ==========================================
# # Get Current User
# # ==========================================

# # get_current_user ရဲ့ task က
# # JWT token ကို verify လုပ်ပြီး
# # current user ကို database ကနေရှာပြီး return ပြန်ပေးတာပါ။

# def get_current_user(
#     token: str = Depends(oauth2_scheme),
#     db: Session = Depends(get_db)
# ):

#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={
#             "WWW-Authenticate": "Bearer"
#         }
#     )

#     try:
#         # Login လုပ်ပြီးရတဲ့ JWT token ကို verify လုပ်တာပါ။
#         # Token ကို decode လုပ်ပြီး user_id ကိုရှာပါတယ်။

#         payload = jwt.decode(
#             token,
#             SECRET_KEY,
#             algorithms=[ALGORITHM]
#         )

#         user_id = payload.get("sub")

#         if user_id is None:
#             raise credentials_exception

#     except JWTError:
#         raise credentials_exception

#     # JWT ထဲက user_id နဲ့
#     # PostgreSQL users table ထဲက user ကိုရှာပါတယ်။

#     user = (
#         db.query(User)
#         .filter(User.id == int(user_id))
#         .first()
#     )

#     if user is None:
#         raise credentials_exception

#     return user


# # ==========================================
# # Role-Based Authorization
# # ==========================================

# # User ရဲ့ role ကိုစစ်ပေးတဲ့ function ပါ။
# # ဥပမာ:
# # require_role("student")
# # require_role("lecturer")
# # require_role("admin")

# def require_role(required_role: str):

#     def role_checker(
#         current_user: User = Depends(get_current_user)
#     ):

#         if current_user.role != required_role:
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="You do not have permission to access this resource"
#             )

#         return current_user

#     return role_checker




from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.utils.jwt import SECRET_KEY, ALGORITHM


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={
            "WWW-Authenticate": "Bearer"
        }
    )

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Admin
    if user_id == "admin":

        return User(
            id=0,
            full_name="Administrator",
            email=payload.get(
                "email",
                "admin@gmail.com"
            ),
            password_hash="",
            role="admin",
            class_year=None,
            is_active=True
        )

    try:

        user_id = int(user_id)

    except (TypeError, ValueError):

        raise credentials_exception

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if user is None:
        raise credentials_exception

    return user


def require_role(required_role: str):

    def role_checker(
        current_user: User = Depends(
            get_current_user
        )
    ):

        if current_user.role != required_role:

            raise HTTPException(
                status_code=403,
                detail="You do not have permission"
            )

        return current_user

    return role_checker