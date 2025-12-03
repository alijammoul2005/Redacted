from sqlalchemy.orm import Session
from models.employee import Department
from schemas.department import DepartmentCreate, DepartmentUpdate
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)


class DepartmentService:

    @staticmethod
    def create_department(dept_data: DepartmentCreate, db: Session):
        """Create a new department"""
        logger.info(f"Creating department: {dept_data.name}")

        try:
            # Check if department name already exists
            existing = db.query(Department).filter(Department.name == dept_data.name).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Department with this name already exists"
                )

            new_department = Department(
                name=dept_data.name,
                extension=dept_data.extension,
                email=dept_data.email,
                staff_count=0
            )

            db.add(new_department)
            db.commit()
            db.refresh(new_department)

            logger.info(f"Department created: {new_department.department_id}")
            return new_department

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create department: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create department"
            )

    @staticmethod
    def get_all_departments(db: Session):
        """Get all departments"""
        logger.info("Fetching all departments")

        try:
            departments = db.query(Department).all()
            logger.info(f"Found {len(departments)} departments")
            return departments

        except Exception as e:
            logger.error(f"Failed to fetch departments: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch departments"
            )

    @staticmethod
    def get_department_by_id(department_id: int, db: Session):
        """Get department by ID"""
        department = db.query(Department).filter(
            Department.department_id == department_id
        ).first()

        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found"
            )

        return department

    @staticmethod
    def update_department(department_id: int, update_data: DepartmentUpdate, db: Session):
        """Update department information"""
        logger.info(f"Updating department: {department_id}")

        try:
            department = db.query(Department).filter(
                Department.department_id == department_id
            ).first()

            if not department:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Department not found"
                )

            if update_data.name:
                department.name = update_data.name
            if update_data.extension:
                department.extension = update_data.extension
            if update_data.email:
                department.email = update_data.email

            db.commit()
            db.refresh(department)

            logger.info(f"Department updated: {department_id}")
            return department

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update department: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update department"
            )

    @staticmethod
    def delete_department(department_id: int, db: Session):
        """Delete a department (only if no employees)"""
        logger.info(f"Deleting department: {department_id}")

        try:
            department = db.query(Department).filter(
                Department.department_id == department_id
            ).first()

            if not department:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Department not found"
                )

            if department.staff_count > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete department with active employees"
                )

            db.delete(department)
            db.commit()

            logger.info(f"Department deleted: {department_id}")
            return {"message": "Department deleted successfully"}

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete department: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete department"
            )
