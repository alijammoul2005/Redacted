from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from services.announcement_service import AnnouncementService
from models.announcement import Announcement
from typing import List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/homepage")
async def get_homepage_data(db: Session = Depends(get_db)):
    """
    Get all data for the main homepage/landing page

    Returns:
    - Latest news (last 7 days)
    - Upcoming events (next 7 days)
    - Urgent announcements
    - Emergency notices
    - Recent tenders
    """
    logger.info("Fetching homepage data")

    try:
        # Get latest news (last 7 days)
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        latest_news = db.query(Announcement).filter(
            Announcement.is_active == True,
            Announcement.category == "News",
            Announcement.issue_date >= one_week_ago
        ).order_by(Announcement.issue_date.desc()).limit(5).all()

        # Get upcoming events (next 7 days)
        next_week = datetime.utcnow() + timedelta(days=7)
        upcoming_events = db.query(Announcement).filter(
            Announcement.is_active == True,
            Announcement.category == "Event",
            Announcement.event_date != None,
            Announcement.event_date >= datetime.utcnow(),
            Announcement.event_date <= next_week
        ).order_by(Announcement.event_date.asc()).limit(5).all()

        # Get urgent/emergency announcements
        urgent_announcements = db.query(Announcement).filter(
            Announcement.is_active == True,
            Announcement.priority.in_(["HIGH", "URGENT"])
        ).order_by(Announcement.issue_date.desc()).limit(3).all()

        # Get emergency notices
        emergency_notices = db.query(Announcement).filter(
            Announcement.is_active == True,
            Announcement.category == "Emergency"
        ).order_by(Announcement.issue_date.desc()).limit(3).all()

        # Get recent tenders
        recent_tenders = db.query(Announcement).filter(
            Announcement.is_active == True,
            Announcement.category == "Tender",
            (Announcement.expiry_date == None) | (Announcement.expiry_date > datetime.utcnow())
        ).order_by(Announcement.issue_date.desc()).limit(5).all()

        # Get maintenance notices
        maintenance_notices = db.query(Announcement).filter(
            Announcement.is_active == True,
            Announcement.category == "Maintenance"
        ).order_by(Announcement.issue_date.desc()).limit(3).all()

        return {
            "latest_news": latest_news,
            "upcoming_events": upcoming_events,
            "urgent_announcements": urgent_announcements,
            "emergency_notices": emergency_notices,
            "recent_tenders": recent_tenders,
            "maintenance_notices": maintenance_notices,
            "last_updated": datetime.utcnow()
        }

    except Exception as e:
        logger.error(f"Failed to fetch homepage data: {str(e)}", exc_info=True)
        return {
            "latest_news": [],
            "upcoming_events": [],
            "urgent_announcements": [],
            "emergency_notices": [],
            "recent_tenders": [],
            "maintenance_notices": [],
            "last_updated": datetime.utcnow(),
            "error": "Failed to load some content"
        }


@router.get("/news")
async def get_news(
        days: int = Query(7, ge=1, le=30),
        limit: int = Query(10, ge=1, le=50),
        db: Session = Depends(get_db)
):
    """
    Get latest news articles

    - **days**: How many days back to fetch news (default 7)
    - **limit**: Maximum number of news items (default 10)
    """
    date_from = datetime.utcnow() - timedelta(days=days)

    news = db.query(Announcement).filter(
        Announcement.is_active == True,
        Announcement.category == "News",
        Announcement.issue_date >= date_from
    ).order_by(Announcement.issue_date.desc()).limit(limit).all()

    return {
        "news": news,
        "total": len(news),
        "period_days": days
    }


@router.get("/events")
async def get_events(
        upcoming_only: bool = Query(True),
        limit: int = Query(10, ge=1, le=50),
        db: Session = Depends(get_db)
):
    """
    Get municipal events

    - **upcoming_only**: If true, only returns future events (default true)
    - **limit**: Maximum number of events (default 10)
    """
    query = db.query(Announcement).filter(
        Announcement.is_active == True,
        Announcement.category == "Event",
        Announcement.event_date != None
    )

    if upcoming_only:
        query = query.filter(Announcement.event_date >= datetime.utcnow())

    events = query.order_by(Announcement.event_date.asc()).limit(limit).all()

    return {
        "events": events,
        "total": len(events),
        "upcoming_only": upcoming_only
    }


@router.get("/tenders")
async def get_tenders(
        active_only: bool = Query(True),
        limit: int = Query(10, ge=1, le=50),
        db: Session = Depends(get_db)
):
    """
    Get tender announcements

    - **active_only**: If true, only returns active tenders (default true)
    - **limit**: Maximum number of tenders (default 10)
    """
    query = db.query(Announcement).filter(
        Announcement.is_active == True,
        Announcement.category == "Tender"
    )

    if active_only:
        query = query.filter(
            (Announcement.expiry_date == None) |
            (Announcement.expiry_date > datetime.utcnow())
        )

    tenders = query.order_by(Announcement.issue_date.desc()).limit(limit).all()

    return {
        "tenders": tenders,
        "total": len(tenders),
        "active_only": active_only
    }


@router.get("/emergencies")
async def get_emergency_notices(
        limit: int = Query(5, ge=1, le=20),
        db: Session = Depends(get_db)
):
    """
    Get emergency and urgent notices

    - **limit**: Maximum number of notices (default 5)
    """
    emergencies = db.query(Announcement).filter(
        Announcement.is_active == True,
        Announcement.category == "Emergency"
    ).order_by(Announcement.issue_date.desc()).limit(limit).all()

    urgent = db.query(Announcement).filter(
        Announcement.is_active == True,
        Announcement.priority == "URGENT",
        Announcement.category != "Emergency"
    ).order_by(Announcement.issue_date.desc()).limit(limit).all()

    return {
        "emergency_notices": emergencies,
        "urgent_announcements": urgent,
        "total": len(emergencies) + len(urgent)
    }


@router.get("/statistics")
async def get_public_statistics(db: Session = Depends(get_db)):
    """
    Get public statistics for the municipality

    Returns counts of active announcements by category
    """
    from sqlalchemy import func

    stats = db.query(
        Announcement.category,
        func.count(Announcement.announcement_id).label('count')
    ).filter(
        Announcement.is_active == True
    ).group_by(Announcement.category).all()

    return {
        "active_announcements": dict((cat.value, count) for cat, count in stats),
        "total_active": sum(count for _, count in stats)
    }

