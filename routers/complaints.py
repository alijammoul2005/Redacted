from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
from schemas.complaint import (
    ComplaintCreate,
    ComplaintResponse,
    ComplaintDetailResponse,
    ComplaintUpdate,
    ComplaintResponseCreate,
    ComplaintResponseResponse
)
from services.complaint_service import ComplaintService
from utils.dependencies import get_current_user
from models.account import Account
from models.citizen import Citizen
from models.employee import Employee
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================
# CITIZEN ENDPOINTS
# ============================================

@router.post("/", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
async def create_complaint(
        complaint_data: ComplaintCreate,
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Submit a new complaint (Citizens only)

    - **category**: Type of complaint
    - **title**: Brief title
    - **description**: Detailed description
    - **location**: Optional location details
    """
    logger.info(f"Complaint submission by user: {current_user.email}")

    citizen = db.query(Citizen).filter(Citizen.account_id == current_user.account_id).first()

    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only citizens can submit complaints"
        )

    return ComplaintService.create_complaint(complaint_data, citizen.citizen_id, db)


@router.get("/my-complaints", response_model=List[ComplaintResponse])
async def get_my_complaints(
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get all complaints submitted by current citizen
    """
    citizen = db.query(Citizen).filter(Citizen.account_id == current_user.account_id).first()

    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only citizens can view their complaints"
        )

    return ComplaintService.get_citizen_complaints(citizen.citizen_id, db)


@router.get("/{complaint_id}", response_model=ComplaintDetailResponse)
async def get_complaint_details(
        complaint_id: int,
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific complaint
    """
    complaint_detail = ComplaintService.get_complaint_by_id(complaint_id, db)

    # Authorization check
    citizen = db.query(Citizen).filter(Citizen.account_id == current_user.account_id).first()
    employee = db.query(Employee).filter(Employee.account_id == current_user.account_id).first()

    # Citizens can only view their own complaints
    if citizen and not employee:
        if complaint_detail["citizen_id"] != citizen.citizen_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own complaints"
            )

    return complaint_detail


@router.delete("/{complaint_id}")
async def delete_complaint(
        complaint_id: int,
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Delete a complaint (only if SUBMITTED status)
    """
    citizen = db.query(Citizen).filter(Citizen.account_id == current_user.account_id).first()

    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only citizens can delete their complaints"
        )

    return ComplaintService.delete_complaint(complaint_id, citizen.citizen_id, db)


# ============================================
# EMPLOYEE ENDPOINTS
# ============================================

@router.get("/all/complaints", response_model=List[ComplaintResponse])
async def get_all_complaints(
        status_filter: Optional[str] = Query(None),
        category_filter: Optional[str] = Query(None),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get all complaints (Employees only)
    """
    employee = db.query(Employee).filter(Employee.account_id == current_user.account_id).first()

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only employees can view all complaints"
        )

    return ComplaintService.get_all_complaints(db, status_filter, category_filter, skip, limit)


@router.put("/{complaint_id}/assign/{employee_id}")
async def assign_complaint(
        complaint_id: int,
        employee_id: int,
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Assign complaint to an employee (Managers only)
    """
    employee = db.query(Employee).filter(Employee.account_id == current_user.account_id).first()

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only employees can assign complaints"
        )

    return ComplaintService.assign_complaint(complaint_id, employee_id, db)


@router.put("/{complaint_id}/status")
async def update_complaint_status(
        complaint_id: int,
        update_data: ComplaintUpdate,
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Update complaint status (Employees only)
    """
    employee = db.query(Employee).filter(Employee.account_id == current_user.account_id).first()

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only employees can update complaint status"
        )

    return ComplaintService.update_complaint_status(complaint_id, update_data, db)


@router.post("/{complaint_id}/respond", response_model=ComplaintResponseResponse)
async def add_complaint_response(
        complaint_id: int,
        response_data: ComplaintResponseCreate,
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Add a response to a complaint (Employees only)
    """
    employee = db.query(Employee).filter(Employee.account_id == current_user.account_id).first()

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only employees can respond to complaints"
        )

    return ComplaintService.add_response(complaint_id, employee.employee_id, response_data, db)
