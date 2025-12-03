# ============================================
# FILE: routers/citizens.py
# ============================================
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from utils.dependencies import get_current_user
from models.account import Account
from models.citizen import Citizen
from models.request import Request
from models.payment import Payment
from models.complaint import Complaint
from models.feedback import Feedback
from models.notification import Notification
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================
# CITIZEN PROFILE ENDPOINTS
# ============================================

@router.get("/me")
async def get_my_profile(
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get current citizen's full profile information

    Returns complete citizen details including account info
    """
    logger.info(f"Fetching profile for user: {current_user.email}")

    citizen = db.query(Citizen).filter(Citizen.account_id == current_user.account_id).first()

    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citizen profile not found"
        )

    return {
        "citizen_id": citizen.citizen_id,
        "account_id": current_user.account_id,
        "email": current_user.email,
        "phone": current_user.phone,
        "national_id": citizen.national_id,
        "first_name": citizen.first_name,
        "middle_name": citizen.middle_name,
        "last_name": citizen.last_name,
        "full_name": f"{citizen.first_name} {citizen.middle_name or ''} {citizen.last_name}".strip(),
        "date_of_birth": citizen.date_of_birth,
        "father_name": citizen.father_name,
        "mother_name": citizen.mother_name,
        "address": citizen.address,
        "marital_status": citizen.marital_status,
        "resident_status": citizen.resident_status,
        "account_created": current_user.created_at,
        "is_active": current_user.is_active == 1
    }


@router.put("/me")
async def update_my_profile(
        phone: Optional[str] = None,
        address: Optional[str] = None,
        marital_status: Optional[str] = None,
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Update current citizen's profile

    Allows updating: phone, address, marital_status
    """
    logger.info(f"Updating profile for user: {current_user.email}")

    citizen = db.query(Citizen).filter(Citizen.account_id == current_user.account_id).first()

    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citizen profile not found"
        )

    try:
        # Update account fields
        if phone:
            current_user.phone = phone

        # Update citizen fields
        if address:
            citizen.address = address
        if marital_status:
            citizen.marital_status = marital_status

        db.commit()
        db.refresh(citizen)
        db.refresh(current_user)

        logger.info(f"Profile updated successfully for: {current_user.email}")

        return {
            "message": "Profile updated successfully",
            "updated_fields": {
                "phone": phone is not None,
                "address": address is not None,
                "marital_status": marital_status is not None
            }
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update profile: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


# ============================================
# CITIZEN DASHBOARD / STATISTICS
# ============================================

@router.get("/dashboard/stats")
async def get_dashboard_statistics(
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get citizen dashboard statistics

    Returns:
    - Total requests (by status)
    - Total payments
    - Total complaints
    - Unread notifications count
    """
    logger.info(f"Fetching dashboard stats for: {current_user.email}")

    citizen = db.query(Citizen).filter(Citizen.account_id == current_user.account_id).first()

    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citizen profile not found"
        )

    try:
        # Request statistics
        total_requests = db.query(Request).filter(Request.citizen_id == citizen.citizen_id).count()
        submitted_requests = db.query(Request).filter(
            Request.citizen_id == citizen.citizen_id,
            Request.status == "SUBMITTED"
        ).count()
        under_review_requests = db.query(Request).filter(
            Request.citizen_id == citizen.citizen_id,
            Request.status == "UNDER_REVIEW"
        ).count()
        approved_requests = db.query(Request).filter(
            Request.citizen_id == citizen.citizen_id,
            Request.status == "APPROVED"
        ).count()
        completed_requests = db.query(Request).filter(
            Request.citizen_id == citizen.citizen_id,
            Request.status == "COMPLETED"
        ).count()

        # Payment statistics
        request_ids = [r.request_id for r in db.query(Request).filter(
            Request.citizen_id == citizen.citizen_id
        ).all()]

        total_payments = db.query(Payment).filter(Payment.request_id.in_(request_ids)).count()
        total_amount_paid = db.query(Payment).filter(
            Payment.request_id.in_(request_ids),
            Payment.status == "COMPLETED"
        ).count()

        # Complaint statistics
        total_complaints = db.query(Complaint).filter(
            Complaint.citizen_id == citizen.citizen_id
        ).count()
        open_complaints = db.query(Complaint).filter(
            Complaint.citizen_id == citizen.citizen_id,
            Complaint.status.in_(["SUBMITTED", "UNDER_REVIEW", "IN_PROGRESS"])
        ).count()
        resolved_complaints = db.query(Complaint).filter(
            Complaint.citizen_id == citizen.citizen_id,
            Complaint.status == "RESOLVED"
        ).count()

        # Notification statistics
        unread_notifications = db.query(Notification).filter(
            Notification.citizen_id == citizen.citizen_id,
            Notification.is_read == False
        ).count()

        # Feedback statistics
        total_feedback = db.query(Feedback).filter(
            Feedback.citizen_id == citizen.citizen_id
        ).count()

        return {
            "requests": {
                "total": total_requests,
                "submitted": submitted_requests,
                "under_review": under_review_requests,
                "approved_pending_payment": approved_requests,
                "completed": completed_requests
            },
            "payments": {
                "total_transactions": total_payments,
                "completed_payments": total_amount_paid
            },
            "complaints": {
                "total": total_complaints,
                "open": open_complaints,
                "resolved": resolved_complaints
            },
            "notifications": {
                "unread_count": unread_notifications
            },
            "feedback": {
                "total_submitted": total_feedback
            }
        }

    except Exception as e:
        logger.error(f"Failed to fetch dashboard stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch dashboard statistics"
        )


@router.get("/dashboard/recent-activity")
async def get_recent_activity(
        limit: int = 10,
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get recent activity for citizen dashboard

    Returns recent requests, payments, complaints, and notifications
    """
    logger.info(f"Fetching recent activity for: {current_user.email}")

    citizen = db.query(Citizen).filter(Citizen.account_id == current_user.account_id).first()

    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citizen profile not found"
        )

    try:
        # Recent requests
        recent_requests = db.query(Request).filter(
            Request.citizen_id == citizen.citizen_id
        ).order_by(Request.request_date.desc()).limit(limit).all()

        # Recent notifications
        recent_notifications = db.query(Notification).filter(
            Notification.citizen_id == citizen.citizen_id
        ).order_by(Notification.created_at.desc()).limit(limit).all()

        return {
            "recent_requests": [
                {
                    "request_id": req.request_id,
                    "type": req.request_type,
                    "status": req.status.value,
                    "date": req.request_date
                } for req in recent_requests
            ],
            "recent_notifications": [
                {
                    "notification_id": notif.notification_id,
                    "title": notif.title,
                    "message": notif.message,
                    "is_read": notif.is_read,
                    "created_at": notif.created_at
                } for notif in recent_notifications
            ]
        }

    except Exception as e:
        logger.error(f"Failed to fetch recent activity: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch recent activity"
        )


# ============================================
# PASSWORD CHANGE
# ============================================

@router.put("/change-password")
async def change_password(
        current_password: str,
        new_password: str,
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Change user password

    Requires current password for verification
    """
    from utils.security import verify_password, get_password_hash

    logger.info(f"Password change attempt for: {current_user.email}")

    # Verify current password
    if not verify_password(current_password, current_user.hashed_password):
        logger.warning(f"Invalid current password for: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Validate new password length
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters long"
        )

    try:
        # Update password
        current_user.hashed_password = get_password_hash(new_password)
        db.commit()

        logger.info(f"Password changed successfully for: {current_user.email}")

        return {
            "message": "Password changed successfully"
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to change password: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


# ============================================
# ACCOUNT DEACTIVATION
# ============================================

@router.delete("/deactivate-account")
async def deactivate_account(
        password: str,
        reason: Optional[str] = None,
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Deactivate user account

    Requires password confirmation
    Soft delete - account can be reactivated by admin
    """
    from utils.security import verify_password

    logger.info(f"Account deactivation request for: {current_user.email}")

    # Verify password
    if not verify_password(password, current_user.hashed_password):
        logger.warning(f"Invalid password for account deactivation: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is incorrect"
        )

    try:
        # Deactivate account
        current_user.is_active = 0
        db.commit()

        logger.info(f"Account deactivated: {current_user.email}, Reason: {reason}")

        return {
            "message": "Account deactivated successfully",
            "email": current_user.email
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to deactivate account: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate account"
        )


# ============================================
# TEST ENDPOINT
# ============================================

@router.get("/test")
async def test_citizens():
    """Test endpoint to verify citizens router is working"""
    logger.info("Citizens test endpoint called")
    return {"message": "Citizens router working"}