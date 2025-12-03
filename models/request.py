from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
import enum


class RequestStatus(enum.Enum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PAID = "PAID"
    COMPLETED = "COMPLETED"


class Request(Base):
    __tablename__ = "requests"

    request_id = Column(Integer, primary_key=True, index=True)
    citizen_id = Column(Integer, ForeignKey("citizens.citizen_id"), nullable=False)
    request_type = Column(String(100), nullable=False)
    request_date = Column(DateTime, default=datetime.utcnow)
    description = Column(Text)
    status = Column(Enum(RequestStatus), default=RequestStatus.SUBMITTED)
    assigned_employee_id = Column(Integer, ForeignKey("employees.employee_id"))
    rejection_reason = Column(Text, nullable=True)

    # Relationships
    citizen = relationship("Citizen", back_populates="requests")
    assigned_employee = relationship("Employee", back_populates="assigned_requests")
    payment = relationship("Payment", back_populates="request", uselist=False)
    attachments = relationship("FileAttachment", back_populates="request", cascade="all, delete-orphan")
