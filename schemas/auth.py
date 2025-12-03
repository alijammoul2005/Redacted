from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=50)
    phone: Optional[str] = None

    # Citizen details
    national_id: str = Field(..., min_length=5, max_length=50)
    first_name: str = Field(..., min_length=2, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    date_of_birth: date
    father_name: Optional[str] = Field(None, max_length=100)
    mother_name: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=255)
    marital_status: Optional[str] = Field(None, max_length=50)

    class Config:
        json_schema_extra = {
            "example": {
                "email": "citizen@example.com",
                "password": "SecurePass123",
                "phone": "+961 70 123456",
                "national_id": "12345678",
                "first_name": "John",
                "middle_name": "Michael",
                "last_name": "Doe",
                "date_of_birth": "1990-01-15",
                "father_name": "Robert Doe",
                "mother_name": "Jane Doe",
                "address": "Beirut, Lebanon",
                "marital_status": "Single"
            }
        }


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "email": "citizen@example.com",
                "password": "SecurePass123"
            }
        }


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    role: str  # "citizen" or "employee"


class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordReset(BaseModel):
    email: EmailStr
    reset_code: str
    new_password: str = Field(..., min_length=8, max_length=50)

