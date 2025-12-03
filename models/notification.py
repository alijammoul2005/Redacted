from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
import enum


class NotificationType(enum.Enum):
    REQUEST_UPDATE = "REQUEST_UPDATE"
    PAYMENT_REMINDER = "PAYMENT_REMINDER"
    COMPLAINT_UPDATE = "COMPLAINT_UPDATE"
    ANNOUNCEMENT = "ANNOUNCEMENT"
    DEADLINE_REMINDER = "DEADLINE_REMINDER"
    GENERAL = "GENERAL"


class Notification(Base):
    __tablename__ = "notifications"

    notification_id = Column(Integer, primary_key=True, index=True)
    citizen_id = Column(Integer, ForeignKey("citizens.citizen_id"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Optional links to related entities
    request_id = Column(Integer, ForeignKey("requests.request_id"), nullable=True)
    complaint_id = Column(Integer, ForeignKey("complaints.complaint_id"), nullable=True)
    announcement_id = Column(Integer, ForeignKey("announcements.announcement_id"), nullable=True)

    # Relationships
    citizen = relationship("Citizen", back_populates="notifications")
