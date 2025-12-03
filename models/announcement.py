from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime

from sqlalchemy.orm import relationship

from database import Base

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Enum
from datetime import datetime
from database import Base
import enum


class AnnouncementPriority(enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class AnnouncementCategory(enum.Enum):
    NEWS = "News"
    EVENT = "Event"
    EMERGENCY = "Emergency"
    MAINTENANCE = "Maintenance"
    TENDER = "Tender"
    GENERAL = "General"


class Announcement(Base):
    __tablename__ = "announcements"

    announcement_id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(Enum(AnnouncementCategory), default=AnnouncementCategory.GENERAL)
    priority = Column(Enum(AnnouncementPriority), default=AnnouncementPriority.MEDIUM)
    issue_date = Column(DateTime, default=datetime.utcnow)
    expiry_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("employees.employee_id"), nullable=False)

    # Event specific fields
    event_date = Column(DateTime, nullable=True)
    event_location = Column(String(500), nullable=True)

    # Relationships
    employee = relationship("Employee")




