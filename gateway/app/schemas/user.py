# from pydantic import BaseModel, EmailStr


# class UserRegister(BaseModel):
#     full_name: str
#     email: EmailStr
#     password: str

# class UserLogin(BaseModel):
#     email: EmailStr
#     password: str


# class UserResponse(BaseModel):
#     id: int
#     full_name: str
#     email: EmailStr
#     role: str

#     class Config:
#         from_attributes = True



from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):

    full_name: str
    email: EmailStr
    password: str


class AdminCreateUser(BaseModel):

    full_name: str
    email: EmailStr
    password: str
    role: str
    class_year: str


class UserResponse(BaseModel):

    id: int
    full_name: str
    email: EmailStr
    role: str
    class_year: str | None = None

    class Config:
        from_attributes = True