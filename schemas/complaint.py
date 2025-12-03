from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ComplaintStatusEnum(str, Enum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"


class ComplaintCategoryEnum(str, Enum):
    INFRASTRUCTURE = "Infrastructure"
    SANITATION = "Sanitation"
    WATER_SUPPLY = "Water Supply"
    ELECTRICITY = "Electricity"
    ROAD_DAMAGE = "Road Damage"
    GARBAGE_COLLECTION = "Garbage Collection"
    NOISE_POLLUTION = "Noise Pollution"
    ILLEGAL_CONSTRUCTION = "Illegal Construction"
    OTHER = "Other"


class ComplaintCreate(BaseModel):
    category: ComplaintCategoryEnum
    title: str = Field(..., min_length=5, max_length=255)
    description: str = Field(..., min_length=10, max_length=2000)
    location: Optional[str] = Field(None, max_length=500)

    class Config:
        json_schema_extra = {
            "example": {
                "category": "Road Damage",
                "title": "Large pothole on Main Street",
                "description": "There is a large pothole on Main Street near the market that is causing traffic issues and vehicle damage.",
                "location": "Main Street, near Central Market, Beirut"
            }
        }


class ComplaintResponse(BaseModel):
    complaint_id: int
    citizen_id: int
    category: str
    title: str
    description: str
    location: Optional[str]
    status: str
    submission_date: datetime
    assigned_employee_id: Optional[int]
    resolution_notes: Optional[str]
    resolved_date: Optional[datetime]

    class Config:
        from_attributes = True


# Define ResponseDetail BEFORE ComplaintDetailResponse
class ResponseDetail(BaseModel):
    response_id: int
    employee_name: str
    message: str
    response_date: datetime


# Now define ComplaintDetailResponse that uses ResponseDetail
class ComplaintDetailResponse(BaseModel):
    complaint_id: int
    citizen_id: int
    citizen_name: str
    category: str
    title: str
    description: str
    location: Optional[str]
    status: str
    submission_date: datetime
    assigned_employee_id: Optional[int]
    assigned_employee_name: Optional[str]
    resolution_notes: Optional[str]
    resolved_date: Optional[datetime]
    responses: List[ResponseDetail] = []


class ComplaintUpdate(BaseModel):
    status: Optional[ComplaintStatusEnum] = None
    assigned_employee_id: Optional[int] = None
    resolution_notes: Optional[str] = None


class ComplaintResponseCreate(BaseModel):
    message: str = Field(..., min_length=5, max_length=1000)

    class Config:
        json_schema_extra = {
            "example": {
                "message": "We have received your complaint and assigned a team to inspect the site. We will update you within 48 hours."
            }
        }


class ComplaintResponseResponse(BaseModel):
    response_id: int
    complaint_id: int
    employee_id: int
    message: str
    response_date: datetime

    class Config:
        from_attributes = True