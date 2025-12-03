from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class AccountResponse(BaseModel):
    account_id: int
    email: EmailStr
    phone: Optional[str]
    created_at: datetime
    is_active: int

    class Config:
        from_attributes = True

