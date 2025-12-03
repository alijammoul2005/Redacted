from sqlalchemy.orm import Session
from sqlalchemy import func
from models.feedback import Feedback
from models.citizen import Citizen
from models.request import Request
from schemas.feedback import FeedbackCreate
from fastapi import HTTPException, status
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class FeedbackService:

    @staticmethod
    def create_feedback(feedback_data: FeedbackCreate, citizen_id: int, db: Session):
        """Create new feedback"""
        logger.info(f"Creating feedback for citizen_id: {citizen_id}")

        try:
            # If request_id provided, verify it belongs to citizen
            if feedback_data.request_id:
                request = db.query(Request).filter(
                    Request.request_id == feedback_data.request_id,
                    Request.citizen_id == citizen_id
                ).first()

                if not request:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Request not found or does not belong to you"
                    )

            new_feedback = Feedback(
                citizen_id=citizen_id,
                request_id=feedback_data.request_id,
                rating=feedback_data.rating,
                comment=feedback_data.comment,
                created_at=datetime.utcnow()
            )

            db.add(new_feedback)
            db.commit()
            db.refresh(new_feedback)

            logger.info(f"Feedback created: feedback_id={new_feedback.feedback_id}")
            return new_feedback

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create feedback: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create feedback"
            )

    @staticmethod
    def get_citizen_feedbacks(citizen_id: int, db: Session):
        """Get all feedbacks by a citizen"""
        logger.info(f"Fetching feedbacks for citizen_id: {citizen_id}")

        try:
            feedbacks = db.query(Feedback).filter(
                Feedback.citizen_id == citizen_id
            ).order_by(Feedback.created_at.desc()).all()

            result = []
            for feedback in feedbacks:
                citizen = db.query(Citizen).filter(Citizen.citizen_id == citizen_id).first()
                citizen_name = f"{citizen.first_name} {citizen.last_name}" if citizen else "Unknown"

                request_type = None
                if feedback.request_id:
                    request = db.query(Request).filter(Request.request_id == feedback.request_id).first()
                    request_type = request.request_type if request else None

                result.append({
                    "feedback_id": feedback.feedback_id,
                    "citizen_id": feedback.citizen_id,
                    "citizen_name": citizen_name,
                    "request_id": feedback.request_id,
                    "request_type": request_type,
                    "rating": feedback.rating,
                    "comment": feedback.comment,
                    "created_at": feedback.created_at
                })

            logger.info(f"Found {len(result)} feedbacks")
            return result

        except Exception as e:
            logger.error(f"Failed to fetch feedbacks: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch feedbacks"
            )

    @staticmethod
    def get_all_feedbacks(db: Session, skip: int = 0, limit: int = 100):
        """Get all feedbacks (for employees)"""
        logger.info("Fetching all feedbacks")

        try:
            feedbacks = db.query(Feedback).order_by(
                Feedback.created_at.desc()
            ).offset(skip).limit(limit).all()

            result = []
            for feedback in feedbacks:
                citizen = db.query(Citizen).filter(Citizen.citizen_id == feedback.citizen_id).first()
                citizen_name = f"{citizen.first_name} {citizen.last_name}" if citizen else "Unknown"

                request_type = None
                if feedback.request_id:
                    request = db.query(Request).filter(Request.request_id == feedback.request_id).first()
                    request_type = request.request_type if request else None

                result.append({
                    "feedback_id": feedback.feedback_id,
                    "citizen_id": feedback.citizen_id,
                    "citizen_name": citizen_name,
                    "request_id": feedback.request_id,
                    "request_type": request_type,
                    "rating": feedback.rating,
                    "comment": feedback.comment,
                    "created_at": feedback.created_at
                })

            logger.info(f"Found {len(result)} feedbacks")
            return result

        except Exception as e:
            logger.error(f"Failed to fetch all feedbacks: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch feedbacks"
            )

    @staticmethod
    def get_feedback_statistics(db: Session):
        """Get feedback statistics"""
        logger.info("Calculating feedback statistics")

        try:
            total = db.query(Feedback).count()

            if total == 0:
                return {
                    "total_feedbacks": 0,
                    "average_rating": 0.0,
                    "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
                    "recent_feedbacks": []
                }

            avg_rating = db.query(func.avg(Feedback.rating)).scalar()

            # Rating distribution
            distribution = {}
            for i in range(1, 6):
                count = db.query(Feedback).filter(Feedback.rating == i).count()
                distribution[i] = count

            # Recent feedbacks
            recent = db.query(Feedback).order_by(
                Feedback.created_at.desc()
            ).limit(5).all()

            recent_list = []
            for feedback in recent:
                citizen = db.query(Citizen).filter(Citizen.citizen_id == feedback.citizen_id).first()
                citizen_name = f"{citizen.first_name} {citizen.last_name}" if citizen else "Unknown"

                request_type = None
                if feedback.request_id:
                    request = db.query(Request).filter(Request.request_id == feedback.request_id).first()
                    request_type = request.request_type if request else None

                recent_list.append({
                    "feedback_id": feedback.feedback_id,
                    "citizen_id": feedback.citizen_id,
                    "citizen_name": citizen_name,
                    "request_id": feedback.request_id,
                    "request_type": request_type,
                    "rating": feedback.rating,
                    "comment": feedback.comment,
                    "created_at": feedback.created_at
                })

            return {
                "total_feedbacks": total,
                "average_rating": round(float(avg_rating), 2),
                "rating_distribution": distribution,
                "recent_feedbacks": recent_list
            }

        except Exception as e:
            logger.error(f"Failed to calculate statistics: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to calculate statistics"
            )
