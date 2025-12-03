from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
from schemas.employee import (
    EmployeeRegister,
    EmployeeResponse,
    EmployeeDetailResponse,
    EmployeeUpdate
)
from schemas.department import DepartmentCreate, DepartmentResponse, DepartmentUpdate
from schemas.request import RequestResponse
from services.employee_service import EmployeeService
from services.department_service import DepartmentService
from utils.dependencies import get_current_user
from models.account import Account
from models.employee import Employee
from typing import List
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================
# EMPLOYEE ENDPOINTS
# ============================================

@router.post("/register", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def register_employee(
        employee_data: EmployeeRegister,
        db: Session = Depends(get_db)
):
    """
    Register a new employee (Admin only in production)

    Note: The citizen with the given national_id must already be registered
    """
    # TODO: Add admin-only authorization check
    return EmployeeService.register_employee(employee_data, db)


@router.get("/me", response_model=EmployeeDetailResponse)
async def get_my_employee_profile(
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get current employee's profile information
    """
    return EmployeeService.get_employee_by_account_id(current_user.account_id, db)


@router.get("/all", response_model=List[EmployeeDetailResponse])
async def get_all_employees(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get all employees (Managers/Admins only)
    """
    # Check if user is an employee with appropriate access
    employee = db.query(Employee).filter(Employee.account_id == current_user.account_id).first()

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only employees can access this endpoint"
        )

    # TODO: Check if user has Manager or Administrator clearance

    return EmployeeService.get_all_employees(db, skip, limit)


@router.get("/{employee_id}", response_model=EmployeeDetailResponse)
async def get_employee_by_id(
        employee_id: int,
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get employee details by ID (Employees only)
    """
    # Verify requester is an employee
    requester = db.query(Employee).filter(Employee.account_id == current_user.account_id).first()

    if not requester:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only employees can access this endpoint"
        )

    target_employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()

    if not target_employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    return EmployeeService.get_employee_by_account_id(target_employee.account_id, db)


@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
        employee_id: int,
        update_data: EmployeeUpdate,
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Update employee information (Admins only)
    """
    # TODO: Add admin-only authorization check
    return EmployeeService.update_employee(employee_id, update_data, db)


@router.delete("/{employee_id}")
async def deactivate_employee(
        employee_id: int,
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Deactivate an employee account (Admins only)
    """
    # TODO: Add admin-only authorization check
    return EmployeeService.deactivate_employee(employee_id, db)


@router.get("/{employee_id}/tasks", response_model=List[RequestResponse])
async def get_employee_tasks(
        employee_id: int,
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get all tasks (requests) assigned to an employee

    Employees can only view their own tasks unless they are managers
    """
    requester = db.query(Employee).filter(Employee.account_id == current_user.account_id).first()

    if not requester:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only employees can access this endpoint"
        )

    # Employees can only view their own tasks (unless manager/admin)
    if requester.employee_id != employee_id:
        if requester.access_clearance not in ["Manager", "Administrator"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own tasks"
            )

    return EmployeeService.get_employee_task_queue(employee_id, db)


# ============================================
# DEPARTMENT ENDPOINTS
# ============================================

@router.post("/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
        dept_data: DepartmentCreate,
        db: Session = Depends(get_db)
):
    """
    Create a new department (Admins only)
    """
    # TODO: Add admin-only authorization check
    return DepartmentService.create_department(dept_data, db)


@router.get("/departments/all", response_model=List[DepartmentResponse])
async def get_all_departments(db: Session = Depends(get_db)):
    """
    Get all departments (Public endpoint for registration)
    """
    return DepartmentService.get_all_departments(db)


@router.get("/departments/{department_id}", response_model=DepartmentResponse)
async def get_department(
        department_id: int,
        db: Session = Depends(get_db)
):
    """
    Get department by ID
    """
    return DepartmentService.get_department_by_id(department_id, db)


@router.put("/departments/{department_id}", response_model=DepartmentResponse)
async def update_department(
        department_id: int,
        update_data: DepartmentUpdate,
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Update department information (Admins only)
    """
    # TODO: Add admin-only authorization check
    return DepartmentService.update_department(department_id, update_data, db)


@router.delete("/departments/{department_id}")
async def delete_department(
        department_id: int,
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Delete a department (Admins only, only if no employees)
    """
    # TODO: Add admin-only authorization check
    return DepartmentService.delete_department(department_id, db)



@router.get("/test")
async def test_employees():
    """Test endpoint to verify employees router is working"""
    logger.info("Employees test endpoint called")
    return {"message": "Employees router working"}

