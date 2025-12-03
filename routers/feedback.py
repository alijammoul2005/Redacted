from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
from schemas.feedback import (
    FeedbackCreate,
    FeedbackResponse,
    FeedbackDetailResponse,
    FeedbackStats
)
from services.feedback_service import FeedbackService
from utils.dependencies import get_current_user
from models.account import Account
from models.citizen import Citizen
from models.employee import Employee
from typing import List
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================
# CITIZEN ENDPOINTS
# ============================================

@router.post("/", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_feedback(
        feedback_data: FeedbackCreate,
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Submit feedback/rating (Citizens only)

    - **request_id**: Optional - Link feedback to a specific request
    - **rating**: 1-5 stars
    - **comment**: Optional feedback comment
    """
    logger.info(f"Feedback submission by user: {current_user.email}")

    citizen = db.query(Citizen).filter(Citizen.account_id == current_user.account_id).first()

    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only citizens can submit feedback"
        )

    return FeedbackService.create_feedback(feedback_data, citizen.citizen_id, db)


@router.get("/my-feedbacks", response_model=List[FeedbackDetailResponse])
async def get_my_feedbacks(
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get all feedbacks submitted by current citizen
    """
    citizen = db.query(Citizen).filter(Citizen.account_id == current_user.account_id).first()

    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only citizens can view their feedbacks"
        )

    return FeedbackService.get_citizen_feedbacks(citizen.citizen_id, db)


# ============================================
# EMPLOYEE ENDPOINTS
# ============================================

@router.get("/all/feedbacks", response_model=List[FeedbackDetailResponse])
async def get_all_feedbacks(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get all feedbacks (Employees only)
    """
    employee = db.query(Employee).filter(Employee.account_id == current_user.account_id).first()

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only employees can view all feedbacks"
        )

    return FeedbackService.get_all_feedbacks(db, skip, limit)


@router.get("/statistics", response_model=FeedbackStats)
async def get_feedback_statistics(
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get feedback statistics and analytics (Employees only)

    Returns:
    - Total number of feedbacks
    - Average rating
    - Rating distribution (1-5 stars)
    - Recent feedbacks
    """
    employee = db.query(Employee).filter(Employee.account_id == current_user.account_id).first()

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only employees can view feedback statistics"
        )

    return FeedbackService.get_feedback_statistics(db)
