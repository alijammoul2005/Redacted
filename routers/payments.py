from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
from schemas.payment import (
    PaymentCreate,
    PaymentResponse,
    PaymentDetailResponse,
    PaymentReceiptResponse
)
from services.payment_service import PaymentService
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

@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
        payment_data: PaymentCreate,
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Process a payment for an approved request (Citizens only)

    - **request_id**: The approved request to pay for
    - **payment_method**: Payment method (Credit Card, Debit Card, etc.)
    - **card_number**: Card number (16 digits)
    - **card_holder**: Name on card
    - **cvv**: Card security code
    - **expiry_date**: Card expiry (MM/YY)

    Maximum 3 payment attempts allowed per request
    """
    logger.info(f"Payment request by user: {current_user.email}")

    citizen = db.query(Citizen).filter(Citizen.account_id == current_user.account_id).first()

    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only citizens can make payments"
        )

    return PaymentService.create_payment(payment_data, citizen.citizen_id, db)


@router.get("/my-payments", response_model=List[PaymentDetailResponse])
async def get_my_payments(
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get payment history for the current citizen

    Returns all payments made by the authenticated user
    """
    logger.info(f"Fetching payment history for user: {current_user.email}")

    citizen = db.query(Citizen).filter(Citizen.account_id == current_user.account_id).first()

    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only citizens can view payment history"
        )

    return PaymentService.get_citizen_payments(citizen.citizen_id, db)


@router.get("/{payment_id}", response_model=PaymentDetailResponse)
async def get_payment_details(
        payment_id: int,
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get details of a specific payment

    Citizens can only view their own payments
    Employees can view all payments
    """
    logger.info(f"Fetching payment details: payment_id={payment_id}")

    payment_detail = PaymentService.get_payment_by_id(payment_id, db)

    # Authorization check
    citizen = db.query(Citizen).filter(Citizen.account_id == current_user.account_id).first()
    employee = db.query(Employee).filter(Employee.account_id == current_user.account_id).first()

    # Citizens can only view their own payments
    if citizen and not employee:
        from models.request import Request
        request = db.query(Request).filter(Request.request_id == payment_detail["request_id"]).first()
        if request.citizen_id != citizen.citizen_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own payments"
            )

    return payment_detail


@router.get("/{payment_id}/receipt", response_model=PaymentReceiptResponse)
async def get_payment_receipt(
        payment_id: int,
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get payment receipt (Citizens only, for completed payments)

    Returns a detailed receipt that can be printed or downloaded
    """
    logger.info(f"Receipt request for payment_id: {payment_id}")

    citizen = db.query(Citizen).filter(Citizen.account_id == current_user.account_id).first()

    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only citizens can view receipts"
        )

    return PaymentService.get_payment_receipt(payment_id, citizen.citizen_id, db)


@router.get("/request/{request_id}/payment")
async def get_payment_for_request(
        request_id: int,
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Check if a payment exists for a specific request

    Returns payment details if exists, otherwise null
    """
    payment = PaymentService.get_payment_by_request(request_id, db)

    if not payment:
        return {"message": "No payment found for this request"}

    return PaymentService.get_payment_by_id(payment.payment_id, db)


# ============================================
# EMPLOYEE ENDPOINTS
# ============================================

@router.get("/all/payments", response_model=List[PaymentDetailResponse])
async def get_all_payments(
        status_filter: Optional[str] = Query(None, description="Filter by status"),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get all payments in the system (Employees only)

    - **status_filter**: Optional filter by status (PENDING, COMPLETED, FAILED)
    - **skip**: Pagination offset
    - **limit**: Maximum number of results
    """
    logger.info(f"Fetching all payments by user: {current_user.email}")

    employee = db.query(Employee).filter(Employee.account_id == current_user.account_id).first()

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only employees can view all payments"
        )

    return PaymentService.get_all_payments(db, status_filter, skip, limit)


# ============================================
# PUBLIC ENDPOINTS
# ============================================

@router.get("/fees/structure")
async def get_fee_structure():
    """
    Get the fee structure for all document types (Public endpoint)

    Returns a dictionary of document types and their fees
    """
    return PaymentService.get_fee_structure()


@router.get("/test")
async def test_payments():
    """Test endpoint to verify payments router is working"""
    logger.info("Payments test endpoint called")
    return {"message": "Payments router working"}

