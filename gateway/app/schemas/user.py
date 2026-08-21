from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):

    full_name: str
    email: EmailStr
    password: str


class AdminCreateUser(BaseModel):

    full_name: str
    email: EmailStr
    role: str
    class_year: str
    classes: list[str] = []
    roll_number: str | None = None


class UserResponse(BaseModel):

    id: int
    roll_number: str | None = None
    full_name: str
    email: EmailStr
    role: str
    class_year: str | None = None
    is_active: bool

    class Config:
        from_attributes = True


class AdminUpdateUser(BaseModel):

    class_year: str | None = None
    is_active: bool | None = None