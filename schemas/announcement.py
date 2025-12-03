from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class AnnouncementPriorityEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class AnnouncementCategoryEnum(str, Enum):
    NEWS = "News"
    EVENT = "Event"
    EMERGENCY = "Emergency"
    MAINTENANCE = "Maintenance"
    TENDER = "Tender"
    GENERAL = "General"


class AnnouncementCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=255)
    content: str = Field(..., min_length=10, max_length=5000)
    category: AnnouncementCategoryEnum
    priority: AnnouncementPriorityEnum = AnnouncementPriorityEnum.MEDIUM
    expiry_date: Optional[datetime] = None
    event_date: Optional[datetime] = None
    event_location: Optional[str] = Field(None, max_length=500)

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Road Maintenance Schedule",
                "content": "Main Street will be closed for maintenance from 8 AM to 6 PM on Friday.",
                "category": "Maintenance",
                "priority": "HIGH",
                "expiry_date": "2024-12-31T23:59:59",
                "event_date": None,
                "event_location": None
            }
        }


class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[AnnouncementCategoryEnum] = None
    priority: Optional[AnnouncementPriorityEnum] = None
    expiry_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    event_date: Optional[datetime] = None
    event_location: Optional[str] = None


class AnnouncementResponse(BaseModel):
    announcement_id: int
    title: str
    content: str
    category: str
    priority: str
    issue_date: datetime
    expiry_date: Optional[datetime]
    is_active: bool
    created_by: int
    event_date: Optional[datetime]
    event_location: Optional[str]

    class Config:
        from_attributes = True


class AnnouncementDetailResponse(BaseModel):
    announcement_id: int
    title: str
    content: str
    category: str
    priority: str
    issue_date: datetime
    expiry_date: Optional[datetime]
    is_active: bool
    created_by: int
    created_by_name: str
    event_date: Optional[datetime]
    event_location: Optional[str]
