from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class NotificationCreate(BaseModel):
    citizen_id: int
    title: str = Field(..., min_length=3, max_length=255)
    message: str = Field(..., min_length=5, max_length=1000)
    notification_type: str
    request_id: Optional[int] = None
    complaint_id: Optional[int] = None
    announcement_id: Optional[int] = None


class NotificationResponse(BaseModel):
    notification_id: int
    citizen_id: int
    title: str
    message: str
    notification_type: str
    is_read: bool
    created_at: datetime
    request_id: Optional[int]
    complaint_id: Optional[int]
    announcement_id: Optional[int]

    class Config:
        from_attributes = True


class NotificationStats(BaseModel):
    total_notifications: int
    unread_count: int
    read_count: int
