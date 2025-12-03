from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
import enum


class ComplaintStatus(enum.Enum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"


class ComplaintCategory(enum.Enum):
    INFRASTRUCTURE = "Infrastructure"
    SANITATION = "Sanitation"
    WATER_SUPPLY = "Water Supply"
    ELECTRICITY = "Electricity"
    ROAD_DAMAGE = "Road Damage"
    GARBAGE_COLLECTION = "Garbage Collection"
    NOISE_POLLUTION = "Noise Pollution"
    ILLEGAL_CONSTRUCTION = "Illegal Construction"
    OTHER = "Other"


class Complaint(Base):
    __tablename__ = "complaints"

    complaint_id = Column(Integer, primary_key=True, index=True)
    citizen_id = Column(Integer, ForeignKey("citizens.citizen_id"), nullable=False)
    category = Column(Enum(ComplaintCategory), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String(500))
    status = Column(Enum(ComplaintStatus), default=ComplaintStatus.SUBMITTED)
    submission_date = Column(DateTime, default=datetime.utcnow)
    assigned_employee_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    resolved_date = Column(DateTime, nullable=True)

    # Relationships
    citizen = relationship("Citizen", back_populates="complaints")
    assigned_employee = relationship("Employee", back_populates="assigned_complaints")
    responses = relationship("ComplaintResponse", back_populates="complaint", cascade="all, delete-orphan")
    attachments = relationship("FileAttachment", back_populates="complaint", cascade="all, delete-orphan")


class ComplaintResponse(Base):
    __tablename__ = "complaint_responses"

    response_id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.complaint_id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=False)
    message = Column(Text, nullable=False)
    response_date = Column(DateTime, default=datetime.utcnow)

    # Relationships
    complaint = relationship("Complaint", back_populates="responses")
    employee = relationship("Employee")