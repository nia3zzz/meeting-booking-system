from pydantic import BaseModel, Field, EmailStr


class RegisterUserValidator(BaseModel):
    first_name: str = Field(min_length=3, max_length=12)
    last_name: str = Field(min_length=3, max_length=12)
    email: EmailStr
    password: str = Field(min_length=6, max_length=30)


class LoginUserValidator(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=30)
