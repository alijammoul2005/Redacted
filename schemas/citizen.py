from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class CitizenCreate(BaseModel):
    national_id: str
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    date_of_birth: date
    father_name: Optional[str] = None
    mother_name: Optional[str] = None
    address: Optional[str] = None
    marital_status: Optional[str] = None


class CitizenResponse(BaseModel):
    citizen_id: int
    national_id: str
    first_name: str
    middle_name: Optional[str]
    last_name: str
    date_of_birth: date
    father_name: Optional[str]
    mother_name: Optional[str]
    address: Optional[str]
    marital_status: Optional[str]
    resident_status: bool

    class Config:
        from_attributes = True
