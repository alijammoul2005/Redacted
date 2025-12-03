from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
from schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationStats
)
from services.notification_service import NotificationService
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

@router.get("/my-notifications", response_model=List[NotificationResponse])
async def get_my_notifications(
        unread_only: bool = Query(False),
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get all notifications for current user

    - **unread_only**: If true, returns only unread notifications
    """
    logger.info(f"Fetching notifications for user: {current_user.email}")

    citizen = db.query(Citizen).filter(Citizen.account_id == current_user.account_id).first()

    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only citizens can view notifications"
        )

    return NotificationService.get_citizen_notifications(citizen.citizen_id, unread_only, db)


@router.get("/stats", response_model=NotificationStats)
async def get_notification_stats(
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get notification statistics (total, unread, read count)
    """
    citizen = db.query(Citizen).filter(Citizen.account_id == current_user.account_id).first()

    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only citizens can view notification stats"
        )

    return NotificationService.get_notification_stats(citizen.citizen_id, db)


@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_as_read(
        notification_id: int,
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Mark a notification as read
    """
    citizen = db.query(Citizen).filter(Citizen.account_id == current_user.account_id).first()

    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only citizens can update notifications"
        )

    return NotificationService.mark_as_read(notification_id, citizen.citizen_id, db)


@router.put("/mark-all-read")
async def mark_all_notifications_as_read(
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Mark all notifications as read for current user
    """
    citizen = db.query(Citizen).filter(Citizen.account_id == current_user.account_id).first()

    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only citizens can update notifications"
        )

    return NotificationService.mark_all_as_read(citizen.citizen_id, db)


@router.delete("/{notification_id}")
async def delete_notification(
        notification_id: int,
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Delete a notification
    """
    citizen = db.query(Citizen).filter(Citizen.account_id == current_user.account_id).first()

    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only citizens can delete notifications"
        )

    return NotificationService.delete_notification(notification_id, citizen.citizen_id, db)


# ============================================
# EMPLOYEE ENDPOINTS (Send notifications)
# ============================================

@router.post("/send", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def send_notification(
        notification_data: NotificationCreate,
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Send a notification to a citizen (Employees only)

    This endpoint allows employees to manually send notifications
    """
    logger.info(f"Sending notification by user: {current_user.email}")

    employee = db.query(Employee).filter(Employee.account_id == current_user.account_id).first()

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only employees can send notifications"
        )

    return NotificationService.create_notification(notification_data, db)

