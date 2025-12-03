from sqlalchemy.orm import Session
from models.notification import Notification
from schemas.notification import NotificationCreate
from fastapi import HTTPException, status
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class NotificationService:

    @staticmethod
    def create_notification(notification_data: NotificationCreate, db: Session):
        """Create a new notification"""
        logger.info(f"Creating notification for citizen_id: {notification_data.citizen_id}")

        try:
            new_notification = Notification(
                citizen_id=notification_data.citizen_id,
                title=notification_data.title,
                message=notification_data.message,
                notification_type=notification_data.notification_type,
                is_read=False,
                created_at=datetime.utcnow(),
                request_id=notification_data.request_id,
                complaint_id=notification_data.complaint_id,
                announcement_id=notification_data.announcement_id
            )

            db.add(new_notification)
            db.commit()
            db.refresh(new_notification)

            logger.info(f"Notification created: notification_id={new_notification.notification_id}")
            return new_notification

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create notification: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create notification"
            )

    @staticmethod
    def get_citizen_notifications(citizen_id: int, unread_only: bool = False, db: Session = None):
        """Get all notifications for a citizen"""
        logger.info(f"Fetching notifications for citizen_id: {citizen_id}")

        try:
            query = db.query(Notification).filter(Notification.citizen_id == citizen_id)

            if unread_only:
                query = query.filter(Notification.is_read == False)

            notifications = query.order_by(Notification.created_at.desc()).all()

            logger.info(f"Found {len(notifications)} notifications")
            return notifications

        except Exception as e:
            logger.error(f"Failed to fetch notifications: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch notifications"
            )

    @staticmethod
    def mark_as_read(notification_id: int, citizen_id: int, db: Session):
        """Mark notification as read"""
        logger.info(f"Marking notification {notification_id} as read")

        try:
            notification = db.query(Notification).filter(
                Notification.notification_id == notification_id,
                Notification.citizen_id == citizen_id
            ).first()

            if not notification:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Notification not found"
                )

            notification.is_read = True
            db.commit()
            db.refresh(notification)

            logger.info(f"Notification marked as read")
            return notification

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to mark notification as read: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update notification"
            )

    @staticmethod
    def mark_all_as_read(citizen_id: int, db: Session):
        """Mark all notifications as read for a citizen"""
        logger.info(f"Marking all notifications as read for citizen_id: {citizen_id}")

        try:
            db.query(Notification).filter(
                Notification.citizen_id == citizen_id,
                Notification.is_read == False
            ).update({"is_read": True})

            db.commit()

            logger.info(f"All notifications marked as read")
            return {"message": "All notifications marked as read"}

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to mark all as read: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update notifications"
            )

    @staticmethod
    def get_notification_stats(citizen_id: int, db: Session):
        """Get notification statistics"""
        total = db.query(Notification).filter(Notification.citizen_id == citizen_id).count()
        unread = db.query(Notification).filter(
            Notification.citizen_id == citizen_id,
            Notification.is_read == False
        ).count()

        return {
            "total_notifications": total,
            "unread_count": unread,
            "read_count": total - unread
        }

    @staticmethod
    def delete_notification(notification_id: int, citizen_id: int, db: Session):
        """Delete a notification"""
        logger.info(f"Deleting notification: {notification_id}")

        try:
            notification = db.query(Notification).filter(
                Notification.notification_id == notification_id,
                Notification.citizen_id == citizen_id
            ).first()

            if not notification:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Notification not found"
                )

            db.delete(notification)
            db.commit()

            logger.info(f"Notification deleted successfully")
            return {"message": "Notification deleted successfully"}

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete notification: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete notification"
            )

# TO BE CONTINUED WITH ROUTERS...

