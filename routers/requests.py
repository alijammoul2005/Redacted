from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
from schemas.request import (
    RequestCreate,
    RequestResponse,
    RequestDetailResponse,
    RequestStatusEnum
)
from services.request_service import RequestService
from utils.dependencies import get_current_user
from models.account import Account
from models.citizen import Citizen
from models.employee import Employee
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=RequestResponse, status_code=status.HTTP_201_CREATED)
async def create_request(
        request_data: RequestCreate,
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Create a new document request (Citizens only)

    - **request_type**: Type of document (Building Permit, License, etc.)
    - **description**: Optional description of the request
    """
    logger.info(f"Request creation by user: {current_user.email}")

    # Get citizen_id from account
    citizen = db.query(Citizen).filter(Citizen.account_id == current_user.account_id).first()

    if not citizen:
        logger.warning(f"Non-citizen user attempted to create request: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only citizens can create requests"
        )

    return RequestService.create_request(request_data, citizen.citizen_id, db)


@router.get("/my-requests", response_model=List[RequestResponse])
async def get_my_requests(
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get all requests for the current citizen

    Returns a list of all document requests submitted by the authenticated user
    """
    logger.info(f"Fetching requests for user: {current_user.email}")

    citizen = db.query(Citizen).filter(Citizen.account_id == current_user.account_id).first()

    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only citizens can view their requests"
        )

    return RequestService.get_citizen_requests(citizen.citizen_id, db)


@router.get("/{request_id}", response_model=RequestDetailResponse)
async def get_request_details(
        request_id: int,
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific request

    Citizens can only view their own requests
    Employees can view all requests
    """
    logger.info(f"Fetching request details: request_id={request_id} by {current_user.email}")

    request_detail = RequestService.get_request_by_id(request_id, db)

    # Check authorization
    citizen = db.query(Citizen).filter(Citizen.account_id == current_user.account_id).first()
    employee = db.query(Employee).filter(Employee.account_id == current_user.account_id).first()

    # Citizens can only view their own requests
    if citizen and not employee:
        if request_detail["citizen_id"] != citizen.citizen_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own requests"
            )

    return request_detail


@router.delete("/{request_id}")
async def delete_request(
        request_id: int,
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Delete a request (only if status is SUBMITTED)

    Citizens can only delete their own requests that haven't been processed yet
    """
    logger.info(f"Delete request attempt: request_id={request_id} by {current_user.email}")

    citizen = db.query(Citizen).filter(Citizen.account_id == current_user.account_id).first()

    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only citizens can delete their requests"
        )

    return RequestService.delete_request(request_id, citizen.citizen_id, db)


# ============================================
# EMPLOYEE ENDPOINTS
# ============================================

@router.get("/all/requests", response_model=List[RequestResponse])
async def get_all_requests(
        status_filter: Optional[str] = Query(None, description="Filter by status"),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get all requests in the system (Employees only)

    - **status_filter**: Optional filter by status (SUBMITTED, UNDER_REVIEW, etc.)
    - **skip**: Pagination offset
    - **limit**: Maximum number of results
    """
    logger.info(f"Fetching all requests by user: {current_user.email}")

    # Check if user is an employee
    employee = db.query(Employee).filter(Employee.account_id == current_user.account_id).first()

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only employees can view all requests"
        )

    return RequestService.get_all_requests(db, status_filter, skip, limit)


@router.put("/{request_id}/assign/{employee_id}")
async def assign_request(
        request_id: int,
        employee_id: int,
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Assign a request to an employee (Managers only)

    Changes status to UNDER_REVIEW
    """
    logger.info(f"Assigning request {request_id} to employee {employee_id} by {current_user.email}")

    # Check if user is an employee with manager access
    employee = db.query(Employee).filter(Employee.account_id == current_user.account_id).first()

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only employees can assign requests"
        )

    # TODO: Add role check for managers only

    return RequestService.assign_request_to_employee(request_id, employee_id, db)


@router.put("/{request_id}/status")
async def update_request_status(
        request_id: int,
        new_status: RequestStatusEnum,
        rejection_reason: Optional[str] = None,
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Update request status (Employees only)

    - **new_status**: New status for the request
    - **rejection_reason**: Required if status is REJECTED
    """
    logger.info(f"Updating request {request_id} status to {new_status} by {current_user.email}")

    # Check if user is an employee
    employee = db.query(Employee).filter(Employee.account_id == current_user.account_id).first()

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only employees can update request status"
        )

    if new_status == RequestStatusEnum.REJECTED and not rejection_reason:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rejection reason is required when rejecting a request"
        )

    return RequestService.update_request_status(request_id, new_status, rejection_reason, db)


@router.get("/test")
async def test_requests():
    """Test endpoint to verify requests router is working"""
    logger.info("Requests test endpoint called")
    return {"message": "Requests router working"}
