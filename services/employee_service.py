from sqlalchemy.orm import Session
from models.account import Account
from models.citizen import Citizen
from models.employee import Employee, Department
from models.request import Request
from schemas.employee import EmployeeRegister, EmployeeUpdate
from utils.security import get_password_hash
from fastapi import HTTPException, status
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EmployeeService:

    @staticmethod
    def register_employee(employee_data: EmployeeRegister, db: Session):
        """Register a new employee (must be existing citizen)"""
        logger.info(f"Employee registration attempt for email: {employee_data.email}")

        # Find citizen by national_id
        citizen = db.query(Citizen).filter(
            Citizen.national_id == employee_data.national_id
        ).first()

        if not citizen:
            logger.warning(f"Registration failed: Citizen not found - {employee_data.national_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Citizen with this national ID not found. Please register as citizen first."
            )

        # Check if this citizen is already an employee
        existing_employee = db.query(Employee).filter(
            Employee.citizen_id == citizen.citizen_id
        ).first()

        if existing_employee:
            logger.warning(f"Registration failed: Citizen is already an employee - {employee_data.national_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This citizen is already registered as an employee"
            )

        # If citizen doesn't have an account, create one with the new email
        # If citizen has an account, use the existing one
        if not citizen.account_id:
            # Check if email already exists
            existing_account = db.query(Account).filter(Account.email == employee_data.email).first()
            if existing_account:
                logger.warning(f"Registration failed: Email already exists - {employee_data.email}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )

            # Create new account
            new_account = Account(
                email=employee_data.email,
                phone=employee_data.phone,
                hashed_password=get_password_hash(employee_data.password),
                created_at=datetime.utcnow(),
                is_active=1,
                failed_login_attempts=0
            )
            db.add(new_account)
            db.flush()

            # Link account to citizen
            citizen.account_id = new_account.account_id
            account_id = new_account.account_id
        else:
            # Use existing account
            account_id = citizen.account_id
            logger.info(f"Using existing account for citizen: {employee_data.national_id}")

        # Check if department exists
        department = db.query(Department).filter(
            Department.department_id == employee_data.department_id
        ).first()

        if not department:
            logger.warning(f"Registration failed: Department not found - {employee_data.department_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found"
            )

        try:
            # Create account
            new_account = Account(
                email=employee_data.email,
                phone=employee_data.phone,
                hashed_password=get_password_hash(employee_data.password),
                created_at=datetime.utcnow(),
                is_active=1,
                failed_login_attempts=0
            )
            db.add(new_account)
            db.flush()

            # Update citizen's account_id
            citizen.account_id = new_account.account_id

            # Create employee record
            new_employee = Employee(
                citizen_id=citizen.citizen_id,
                position=employee_data.position,
                employment_type=employee_data.employment_type.value,
                access_clearance=employee_data.access_clearance.value,
                department_id=employee_data.department_id,
                start_date=employee_data.start_date,
                salary=employee_data.salary,
                account_id=new_account.account_id
            )
            db.add(new_employee)

            # Update department staff count
            department.staff_count += 1

            db.commit()
            db.refresh(new_employee)

            logger.info(f"Employee registered successfully: {employee_data.email}")
            return new_employee

        except Exception as e:
            db.rollback()
            logger.error(f"Employee registration failed: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Employee registration failed"
            )

    @staticmethod
    def get_employee_by_account_id(account_id: int, db: Session):
        """Get employee by account ID"""
        employee = db.query(Employee).filter(Employee.account_id == account_id).first()

        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )

        # Get citizen and account details
        citizen = db.query(Citizen).filter(Citizen.citizen_id == employee.citizen_id).first()
        account = db.query(Account).filter(Account.account_id == account_id).first()
        department = db.query(Department).filter(
            Department.department_id == employee.department_id
        ).first()

        full_name = f"{citizen.first_name} {citizen.middle_name or ''} {citizen.last_name}".strip()

        return {
            "employee_id": employee.employee_id,
            "citizen_id": employee.citizen_id,
            "full_name": full_name,
            "email": account.email,
            "phone": account.phone,
            "position": employee.position,
            "employment_type": employee.employment_type,
            "access_clearance": employee.access_clearance,
            "department_id": employee.department_id,
            "department_name": department.name if department else "Unknown",
            "start_date": employee.start_date,
            "end_date": employee.end_date,
            "salary": employee.salary,
            "is_active": account.is_active == 1
        }

    @staticmethod
    def get_all_employees(db: Session, skip: int = 0, limit: int = 100):
        """Get all employees"""
        logger.info(f"Fetching all employees")

        try:
            employees = db.query(Employee).offset(skip).limit(limit).all()

            result = []
            for emp in employees:
                citizen = db.query(Citizen).filter(Citizen.citizen_id == emp.citizen_id).first()
                account = db.query(Account).filter(Account.account_id == emp.account_id).first()
                department = db.query(Department).filter(
                    Department.department_id == emp.department_id
                ).first()

                full_name = f"{citizen.first_name} {citizen.middle_name or ''} {citizen.last_name}".strip()

                result.append({
                    "employee_id": emp.employee_id,
                    "citizen_id": emp.citizen_id,
                    "full_name": full_name,
                    "email": account.email,
                    "phone": account.phone,
                    "position": emp.position,
                    "employment_type": emp.employment_type,
                    "access_clearance": emp.access_clearance,
                    "department_id": emp.department_id,
                    "department_name": department.name if department else "Unknown",
                    "start_date": emp.start_date,
                    "end_date": emp.end_date,
                    "salary": emp.salary,
                    "is_active": account.is_active == 1
                })

            logger.info(f"Found {len(result)} employees")
            return result

        except Exception as e:
            logger.error(f"Failed to fetch employees: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch employees"
            )

    @staticmethod
    def update_employee(employee_id: int, update_data: EmployeeUpdate, db: Session):
        """Update employee information"""
        logger.info(f"Updating employee: {employee_id}")

        try:
            employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()

            if not employee:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Employee not found"
                )

            # Update fields if provided
            if update_data.position:
                employee.position = update_data.position
            if update_data.employment_type:
                employee.employment_type = update_data.employment_type.value
            if update_data.access_clearance:
                employee.access_clearance = update_data.access_clearance.value
            if update_data.department_id:
                # Check if new department exists
                new_dept = db.query(Department).filter(
                    Department.department_id == update_data.department_id
                ).first()
                if not new_dept:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Department not found"
                    )

                # Update staff counts
                old_dept = db.query(Department).filter(
                    Department.department_id == employee.department_id
                ).first()
                if old_dept:
                    old_dept.staff_count -= 1
                new_dept.staff_count += 1

                employee.department_id = update_data.department_id

            if update_data.salary is not None:
                employee.salary = update_data.salary
            if update_data.end_date:
                employee.end_date = update_data.end_date

            db.commit()
            db.refresh(employee)

            logger.info(f"Employee updated successfully: {employee_id}")
            return employee

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update employee: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update employee"
            )

    @staticmethod
    def deactivate_employee(employee_id: int, db: Session):
        """Deactivate an employee account"""
        logger.info(f"Deactivating employee: {employee_id}")

        try:
            employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()

            if not employee:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Employee not found"
                )

            # Deactivate account
            account = db.query(Account).filter(Account.account_id == employee.account_id).first()
            account.is_active = 0

            # Set end date if not set
            if not employee.end_date:
                employee.end_date = datetime.utcnow().date()

            # Update department staff count
            department = db.query(Department).filter(
                Department.department_id == employee.department_id
            ).first()
            if department and department.staff_count > 0:
                department.staff_count -= 1

            db.commit()

            logger.info(f"Employee deactivated successfully: {employee_id}")
            return {"message": "Employee deactivated successfully"}

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to deactivate employee: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to deactivate employee"
            )

    @staticmethod
    def get_employee_task_queue(employee_id: int, db: Session):
        """Get all requests assigned to an employee"""
        logger.info(f"Fetching task queue for employee: {employee_id}")

        try:
            requests = db.query(Request).filter(
                Request.assigned_employee_id == employee_id
            ).order_by(Request.request_date.desc()).all()

            logger.info(f"Found {len(requests)} tasks for employee {employee_id}")
            return requests

        except Exception as e:
            logger.error(f"Failed to fetch task queue: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch task queue"
            )
