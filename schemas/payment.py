from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class PaymentStatusEnum(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class PaymentMethodEnum(str, Enum):
    CREDIT_CARD = "Credit Card"
    DEBIT_CARD = "Debit Card"
    BANK_TRANSFER = "Bank Transfer"
    CASH = "Cash"
    E_WALLET = "E-Wallet"


class PaymentCreate(BaseModel):
    request_id: int
    payment_method: PaymentMethodEnum

    # Payment details (simplified for demo)
    card_number: Optional[str] = Field(None, min_length=16, max_length=16)
    card_holder: Optional[str] = None
    cvv: Optional[str] = Field(None, min_length=3, max_length=4)
    expiry_date: Optional[str] = None  # MM/YY format

    class Config:
        json_schema_extra = {
            "example": {
                "request_id": 1,
                "payment_method": "Credit Card",
                "card_number": "4532015112830366",
                "card_holder": "John Doe",
                "cvv": "123",
                "expiry_date": "12/25"
            }
        }


class PaymentResponse(BaseModel):
    payment_id: int
    request_id: int
    amount: float
    payment_date: datetime
    status: str
    transaction_id: Optional[str]
    payment_method: str
    retry_count: int

    class Config:
        from_attributes = True


class PaymentDetailResponse(BaseModel):
    payment_id: int
    request_id: int
    request_type: str
    citizen_name: str
    amount: float
    payment_date: datetime
    status: str
    transaction_id: Optional[str]
    payment_method: str
    retry_count: int


class PaymentReceiptResponse(BaseModel):
    payment_id: int
    transaction_id: str
    request_id: int
    request_type: str
    citizen_name: str
    amount: float
    payment_date: datetime
    payment_method: str
    receipt_number: str
    municipality_info: dict
