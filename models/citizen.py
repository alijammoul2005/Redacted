from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Citizen(Base):
    __tablename__ = "citizens"

    citizen_id = Column(Integer, primary_key=True, index=True)
    national_id = Column(String(50), unique=True, index=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    middle_name = Column(String(100))
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    father_name = Column(String(100))
    mother_name = Column(String(100))
    address = Column(String(255))
    marital_status = Column(String(50))
    resident_status = Column(Boolean, default=True)

    # Relationships
    account_id = Column(Integer, ForeignKey("accounts.account_id"))
    account = relationship("Account", back_populates="citizen")
    requests = relationship("Request", back_populates="citizen")
    feedback = relationship("Feedback", back_populates="citizen")
    complaints = relationship("Complaint", back_populates="citizen")
    notifications = relationship("Notification", back_populates="citizen")