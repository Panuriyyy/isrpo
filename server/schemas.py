from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    last_name: str
    first_name: str
    father_name: str | None = None
    email: EmailStr
    university: str
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    last_name: str
    first_name: str
    father_name: str | None
    email: str
    university: str
