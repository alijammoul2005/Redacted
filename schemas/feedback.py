from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class FeedbackCreate(BaseModel):
    request_id: Optional[int] = None
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
    comment: Optional[str] = Field(None, max_length=1000)

    class Config:
        json_schema_extra = {
            "example": {
                "request_id": 1,
                "rating": 5,
                "comment": "Excellent service! The document was processed quickly and the staff were very helpful."
            }
        }


class FeedbackResponse(BaseModel):
    feedback_id: int
    citizen_id: int
    request_id: Optional[int]
    rating: int
    comment: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class FeedbackDetailResponse(BaseModel):
    feedback_id: int
    citizen_id: int
    citizen_name: str
    request_id: Optional[int]
    request_type: Optional[str]
    rating: int
    comment: Optional[str]
    created_at: datetime


class FeedbackStats(BaseModel):
    total_feedbacks: int
    average_rating: float
    rating_distribution: dict
    recent_feedbacks: List[FeedbackDetailResponse]