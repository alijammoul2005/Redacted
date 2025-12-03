from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class RequestStatusEnum(str, Enum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PAID = "PAID"
    COMPLETED = "COMPLETED"


class RequestTypeEnum(str, Enum):
    BUILDING_PERMIT = "Building Permit"
    BUSINESS_LICENSE = "Business License"
    BIRTH_CERTIFICATE = "Birth Certificate"
    MARRIAGE_CERTIFICATE = "Marriage Certificate"
    RESIDENCY_CERTIFICATE = "Residency Certificate"
    TAX_CLEARANCE = "Tax Clearance"
    LAND_REGISTRY = "Land Registry"
    OTHER = "Other"


class RequestCreate(BaseModel):
    request_type: RequestTypeEnum
    description: Optional[str] = Field(None, max_length=1000)

    class Config:
        json_schema_extra = {
            "example": {
                "request_type": "Building Permit",
                "description": "Request for building permit for residential property at Beirut"
            }
        }


class RequestUpdate(BaseModel):
    status: Optional[RequestStatusEnum] = None
    assigned_employee_id: Optional[int] = None
    rejection_reason: Optional[str] = None


class RequestResponse(BaseModel):
    request_id: int
    citizen_id: int
    request_type: str
    request_date: datetime
    description: Optional[str]
    status: str
    assigned_employee_id: Optional[int]
    rejection_reason: Optional[str]

    class Config:
        from_attributes = True


class RequestDetailResponse(BaseModel):
    request_id: int
    citizen_id: int
    citizen_name: str
    request_type: str
    request_date: datetime
    description: Optional[str]
    status: str
    assigned_employee_id: Optional[int]
    assigned_employee_name: Optional[str]
    rejection_reason: Optional[str]

    class Config:
        from_attributes = True

