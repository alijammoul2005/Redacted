from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
from schemas.announcement import (
    AnnouncementCreate,
    AnnouncementUpdate,
    AnnouncementResponse,
    AnnouncementDetailResponse
)
from services.announcement_service import AnnouncementService
from utils.dependencies import get_current_user
from models.account import Account
from models.employee import Employee
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================
# PUBLIC ENDPOINTS (Anyone can view)
# ============================================

@router.get("/active", response_model=List[AnnouncementResponse])
async def get_active_announcements(
        category: Optional[str] = Query(None),
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=100),
        db: Session = Depends(get_db)
):
    """
    Get all active announcements (Public endpoint)

    - **category**: Optional filter by category
    - **skip**: Pagination offset
    - **limit**: Maximum results
    """
    return AnnouncementService.get_active_announcements(db, category, skip, limit)


@router.get("/events/upcoming", response_model=List[AnnouncementResponse])
async def get_upcoming_events(
        days: int = Query(7, ge=1, le=30),
        db: Session = Depends(get_db)
):
    """
    Get upcoming events within specified days (Public endpoint)

    - **days**: Number of days ahead to look (default 7)
    """
    return AnnouncementService.get_upcoming_events(db, days)


@router.get("/{announcement_id}", response_model=AnnouncementDetailResponse)
async def get_announcement_details(
        announcement_id: int,
        db: Session = Depends(get_db)
):
    """
    Get announcement details by ID (Public endpoint)
    """
    return AnnouncementService.get_announcement_by_id(announcement_id, db)


# ============================================
# EMPLOYEE ENDPOINTS (Create, Update, Delete)
# ============================================

@router.post("/", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED)
async def create_announcement(
        announcement_data: AnnouncementCreate,
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Create a new announcement (Employees only)

    - **title**: Announcement title
    - **content**: Full content/description
    - **category**: News, Event, Emergency, etc.
    - **priority**: LOW, MEDIUM, HIGH, URGENT
    - **expiry_date**: Optional expiration date
    """
    logger.info(f"Creating announcement by user: {current_user.email}")

    employee = db.query(Employee).filter(Employee.account_id == current_user.account_id).first()

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only employees can create announcements"
        )

    return AnnouncementService.create_announcement(announcement_data, employee.employee_id, db)


@router.put("/{announcement_id}", response_model=AnnouncementResponse)
async def update_announcement(
        announcement_id: int,
        update_data: AnnouncementUpdate,
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Update an announcement (Employees only)
    """
    employee = db.query(Employee).filter(Employee.account_id == current_user.account_id).first()

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only employees can update announcements"
        )

    return AnnouncementService.update_announcement(announcement_id, update_data, db)


@router.delete("/{announcement_id}")
async def delete_announcement(
        announcement_id: int,
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Delete/deactivate an announcement (Employees only)
    """
    employee = db.query(Employee).filter(Employee.account_id == current_user.account_id).first()

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only employees can delete announcements"
        )

    return AnnouncementService.delete_announcement(announcement_id, db)

