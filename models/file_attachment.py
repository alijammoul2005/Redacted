from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class FileAttachment(Base):
    __tablename__ = "file_attachments"

    file_id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)  # in bytes
    file_type = Column(String(100), nullable=False)  # MIME type
    uploaded_by = Column(Integer, ForeignKey("citizens.citizen_id"), nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)

    # Link to request or complaint
    request_id = Column(Integer, ForeignKey("requests.request_id"), nullable=True)
    complaint_id = Column(Integer, ForeignKey("complaints.complaint_id"), nullable=True)

    # Relationships
    citizen = relationship("Citizen")
    request = relationship("Request", back_populates="attachments")
    complaint = relationship("Complaint", back_populates="attachments")
