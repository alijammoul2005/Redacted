from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    extension: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Document Services",
                "extension": "101",
                "email": "documents@municipality.com"
            }
        }


class DepartmentResponse(BaseModel):
    department_id: int
    name: str
    extension: Optional[str]
    email: Optional[str]
    staff_count: int

    class Config:
        from_attributes = True


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    extension: Optional[str] = None
    email: Optional[EmailStr] = None
