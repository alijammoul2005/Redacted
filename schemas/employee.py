from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date
from enum import Enum


class EmploymentType(str, Enum):
    FULL_TIME = "Full-Time"
    PART_TIME = "Part-Time"
    CONTRACT = "Contract"
    INTERN = "Intern"


class AccessClearance(str, Enum):
    EMPLOYEE = "Employee"
    MANAGER = "Manager"
    ADMINISTRATOR = "Administrator"


class EmployeeRegister(BaseModel):
    # Account info
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=50)
    phone: Optional[str] = None

    # Personal info (must be existing citizen)
    national_id: str = Field(..., min_length=5, max_length=50)

    # Employment info
    position: str = Field(..., min_length=2, max_length=100)
    employment_type: EmploymentType
    access_clearance: AccessClearance
    department_id: int
    start_date: date
    salary: float = Field(..., gt=0)

    class Config:
        json_schema_extra = {
            "example": {
                "email": "employee@municipality.com",
                "password": "SecurePass123",
                "phone": "+961 70 987654",
                "national_id": "12345678",
                "position": "Document Processing Officer",
                "employment_type": "Full-Time",
                "access_clearance": "Employee",
                "department_id": 1,
                "start_date": "2024-01-01",
                "salary": 2000.00
            }
        }


class EmployeeResponse(BaseModel):
    employee_id: int
    citizen_id: int
    position: str
    employment_type: str
    access_clearance: str
    department_id: int
    start_date: date
    end_date: Optional[date]
    salary: float
    account_id: int

    class Config:
        from_attributes = True


class EmployeeDetailResponse(BaseModel):
    employee_id: int
    citizen_id: int
    full_name: str
    email: str
    phone: Optional[str]
    position: str
    employment_type: str
    access_clearance: str
    department_id: int
    department_name: str
    start_date: date
    end_date: Optional[date]
    salary: float
    is_active: bool


class EmployeeUpdate(BaseModel):
    position: Optional[str] = None
    employment_type: Optional[EmploymentType] = None
    access_clearance: Optional[AccessClearance] = None
    department_id: Optional[int] = None
    salary: Optional[float] = None
    end_date: Optional[date] = None

