from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Department(Base):
    __tablename__ = "departments"

    department_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    extension = Column(String(20))
    email = Column(String(255))
    staff_count = Column(Integer, default=0)

    # Relationships
    employees = relationship("Employee", back_populates="department")


class Employee(Base):
    __tablename__ = "employees"

    employee_id = Column(Integer, primary_key=True, index=True)
    citizen_id = Column(Integer, ForeignKey("citizens.citizen_id"))
    position = Column(String(100))
    employment_type = Column(String(50))
    access_clearance = Column(String(50))
    department_id = Column(Integer, ForeignKey("departments.department_id"))
    start_date = Column(Date)
    end_date = Column(Date, nullable=True)
    salary = Column(Float)

    # Relationships
    account_id = Column(Integer, ForeignKey("accounts.account_id"))
    account = relationship("Account", back_populates="employee")
    department = relationship("Department", back_populates="employees")
    assigned_requests = relationship("Request", back_populates="assigned_employee")
    assigned_complaints = relationship("Complaint", back_populates="assigned_employee")