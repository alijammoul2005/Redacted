from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FileAttachmentResponse(BaseModel):
    file_id: int
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    uploaded_by: int
    upload_date: datetime
    request_id: Optional[int]
    complaint_id: Optional[int]

    class Config:
        from_attributes = True


class FileUploadResponse(BaseModel):
    file_id: int
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    message: str
