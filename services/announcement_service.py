from sqlalchemy.orm import Session
from models.announcement import Announcement
from models.employee import Employee
from models.citizen import Citizen
from schemas.announcement import AnnouncementCreate, AnnouncementUpdate
from fastapi import HTTPException, status
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AnnouncementService:

    @staticmethod
    def create_announcement(announcement_data: AnnouncementCreate, employee_id: int, db: Session):
        """Create a new announcement"""
        logger.info(f"Creating announcement by employee_id: {employee_id}")

        try:
            new_announcement = Announcement(
                title=announcement_data.title,
                content=announcement_data.content,
                category=announcement_data.category,
                priority=announcement_data.priority,
                issue_date=datetime.utcnow(),
                expiry_date=announcement_data.expiry_date,
                is_active=True,
                created_by=employee_id,
                event_date=announcement_data.event_date,
                event_location=announcement_data.event_location
            )

            db.add(new_announcement)
            db.commit()
            db.refresh(new_announcement)

            logger.info(f"Announcement created: announcement_id={new_announcement.announcement_id}")
            return new_announcement

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create announcement: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create announcement"
            )

    @staticmethod
    def get_active_announcements(db: Session, category: str = None, skip: int = 0, limit: int = 100):
        """Get all active announcements"""
        logger.info("Fetching active announcements")

        try:
            query = db.query(Announcement).filter(Announcement.is_active == True)

            # Filter expired announcements
            query = query.filter(
                (Announcement.expiry_date == None) |
                (Announcement.expiry_date > datetime.utcnow())
            )

            if category:
                query = query.filter(Announcement.category == category)

            announcements = query.order_by(
                Announcement.priority.desc(),
                Announcement.issue_date.desc()
            ).offset(skip).limit(limit).all()

            logger.info(f"Found {len(announcements)} active announcements")
            return announcements

        except Exception as e:
            logger.error(f"Failed to fetch announcements: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch announcements"
            )

    @staticmethod
    def get_announcement_by_id(announcement_id: int, db: Session):
        """Get announcement details"""
        announcement = db.query(Announcement).filter(
            Announcement.announcement_id == announcement_id
        ).first()

        if not announcement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Announcement not found"
            )

        # Get employee info
        employee = db.query(Employee).filter(Employee.employee_id == announcement.created_by).first()
        created_by_name = "Unknown"
        if employee:
            citizen = db.query(Citizen).filter(Citizen.citizen_id == employee.citizen_id).first()
            created_by_name = f"{citizen.first_name} {citizen.last_name}" if citizen else "Unknown"

        return {
            "announcement_id": announcement.announcement_id,
            "title": announcement.title,
            "content": announcement.content,
            "category": announcement.category.value,
            "priority": announcement.priority.value,
            "issue_date": announcement.issue_date,
            "expiry_date": announcement.expiry_date,
            "is_active": announcement.is_active,
            "created_by": announcement.created_by,
            "created_by_name": created_by_name,
            "event_date": announcement.event_date,
            "event_location": announcement.event_location
        }

    @staticmethod
    def get_upcoming_events(db: Session, days: int = 7):
        """Get upcoming events"""
        logger.info(f"Fetching events for next {days} days")

        try:
            from datetime import timedelta
            future_date = datetime.utcnow() + timedelta(days=days)

            events = db.query(Announcement).filter(
                Announcement.is_active == True,
                Announcement.category == "Event",
                Announcement.event_date != None,
                Announcement.event_date >= datetime.utcnow(),
                Announcement.event_date <= future_date
            ).order_by(Announcement.event_date.asc()).all()

            logger.info(f"Found {len(events)} upcoming events")
            return events

        except Exception as e:
            logger.error(f"Failed to fetch events: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch events"
            )

    @staticmethod
    def update_announcement(announcement_id: int, update_data: AnnouncementUpdate, db: Session):
        """Update announcement"""
        logger.info(f"Updating announcement: {announcement_id}")

        try:
            announcement = db.query(Announcement).filter(
                Announcement.announcement_id == announcement_id
            ).first()

            if not announcement:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Announcement not found"
                )

            if update_data.title:
                announcement.title = update_data.title
            if update_data.content:
                announcement.content = update_data.content
            if update_data.category:
                announcement.category = update_data.category
            if update_data.priority:
                announcement.priority = update_data.priority
            if update_data.expiry_date is not None:
                announcement.expiry_date = update_data.expiry_date
            if update_data.is_active is not None:
                announcement.is_active = update_data.is_active
            if update_data.event_date is not None:
                announcement.event_date = update_data.event_date
            if update_data.event_location is not None:
                announcement.event_location = update_data.event_location

            db.commit()
            db.refresh(announcement)

            logger.info(f"Announcement updated successfully")
            return announcement

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update announcement: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update announcement"
            )

    @staticmethod
    def delete_announcement(announcement_id: int, db: Session):
        """Delete/deactivate announcement"""
        logger.info(f"Deleting announcement: {announcement_id}")

        try:
            announcement = db.query(Announcement).filter(
                Announcement.announcement_id == announcement_id
            ).first()

            if not announcement:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Announcement not found"
                )

            # Soft delete - just deactivate
            announcement.is_active = False
            db.commit()

            logger.info(f"Announcement deactivated successfully")
            return {"message": "Announcement deleted successfully"}

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete announcement: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete announcement"
            )
