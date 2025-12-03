from sqlalchemy.orm import Session
from models.request import Request, RequestStatus
from models.citizen import Citizen
from models.employee import Employee
from models.account import Account
from schemas.request import RequestCreate, RequestUpdate, RequestStatusEnum
from fastapi import HTTPException, status
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RequestService:

    @staticmethod
    def create_request(request_data: RequestCreate, citizen_id: int, db: Session) -> Request:
        """Create a new document request"""
        logger.info(f"Creating request for citizen_id: {citizen_id}, type: {request_data.request_type}")

        try:
            new_request = Request(
                citizen_id=citizen_id,
                request_type=request_data.request_type.value,
                description=request_data.description,
                request_date=datetime.utcnow(),
                status=RequestStatus.SUBMITTED
            )

            db.add(new_request)
            db.commit()
            db.refresh(new_request)

            logger.info(f"Request created successfully: request_id={new_request.request_id}")
            return new_request

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create request: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create request"
            )

    @staticmethod
    def get_citizen_requests(citizen_id: int, db: Session):
        """Get all requests for a specific citizen"""
        logger.info(f"Fetching requests for citizen_id: {citizen_id}")

        try:
            requests = db.query(Request).filter(
                Request.citizen_id == citizen_id
            ).order_by(Request.request_date.desc()).all()

            logger.info(f"Found {len(requests)} requests for citizen_id: {citizen_id}")
            return requests

        except Exception as e:
            logger.error(f"Failed to fetch requests: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch requests"
            )

    @staticmethod
    def get_request_by_id(request_id: int, db: Session):
        """Get a specific request by ID with detailed information"""
        logger.info(f"Fetching request details for request_id: {request_id}")

        try:
            request = db.query(Request).filter(Request.request_id == request_id).first()

            if not request:
                logger.warning(f"Request not found: request_id={request_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Request not found"
                )

            # Get citizen information
            citizen = db.query(Citizen).filter(Citizen.citizen_id == request.citizen_id).first()
            citizen_name = f"{citizen.first_name} {citizen.last_name}" if citizen else "Unknown"

            # Get employee information if assigned
            employee_name = None
            if request.assigned_employee_id:
                employee = db.query(Employee).filter(
                    Employee.employee_id == request.assigned_employee_id
                ).first()
                if employee:
                    emp_citizen = db.query(Citizen).filter(
                        Citizen.citizen_id == employee.citizen_id
                    ).first()
                    employee_name = f"{emp_citizen.first_name} {emp_citizen.last_name}" if emp_citizen else "Unknown"

            request_detail = {
                "request_id": request.request_id,
                "citizen_id": request.citizen_id,
                "citizen_name": citizen_name,
                "request_type": request.request_type,
                "request_date": request.request_date,
                "description": request.description,
                "status": request.status.value,
                "assigned_employee_id": request.assigned_employee_id,
                "assigned_employee_name": employee_name,
                "rejection_reason": request.rejection_reason
            }

            logger.info(f"Request details fetched successfully for request_id: {request_id}")
            return request_detail

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to fetch request details: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch request details"
            )

    @staticmethod
    def get_all_requests(db: Session, status_filter: str = None, skip: int = 0, limit: int = 100):
        """Get all requests (for employees/managers)"""
        logger.info(f"Fetching all requests with filter: {status_filter}")

        try:
            query = db.query(Request)

            if status_filter:
                try:
                    status_enum = RequestStatus[status_filter.upper()]
                    query = query.filter(Request.status == status_enum)
                except KeyError:
                    logger.warning(f"Invalid status filter: {status_filter}")

            requests = query.order_by(Request.request_date.desc()).offset(skip).limit(limit).all()

            logger.info(f"Found {len(requests)} requests")
            return requests

        except Exception as e:
            logger.error(f"Failed to fetch all requests: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch requests"
            )

    @staticmethod
    def assign_request_to_employee(request_id: int, employee_id: int, db: Session) -> Request:
        """Assign a request to an employee"""
        logger.info(f"Assigning request_id={request_id} to employee_id={employee_id}")

        try:
            # Check if request exists
            request = db.query(Request).filter(Request.request_id == request_id).first()
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Request not found"
                )

            # Check if employee exists
            employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
            if not employee:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Employee not found"
                )

            # Assign and update status
            request.assigned_employee_id = employee_id
            request.status = RequestStatus.UNDER_REVIEW

            db.commit()
            db.refresh(request)

            logger.info(f"Request assigned successfully: request_id={request_id}")
            return request

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to assign request: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to assign request"
            )

    @staticmethod
    def update_request_status(
            request_id: int,
            new_status: RequestStatusEnum,
            rejection_reason: str = None,
            db: Session = None
    ) -> Request:
        """Update request status (approve/reject)"""
        logger.info(f"Updating request_id={request_id} status to {new_status}")

        try:
            request = db.query(Request).filter(Request.request_id == request_id).first()

            if not request:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Request not found"
                )

            # Convert enum to RequestStatus
            status_map = {
                RequestStatusEnum.SUBMITTED: RequestStatus.SUBMITTED,
                RequestStatusEnum.UNDER_REVIEW: RequestStatus.UNDER_REVIEW,
                RequestStatusEnum.APPROVED: RequestStatus.APPROVED,
                RequestStatusEnum.REJECTED: RequestStatus.REJECTED,
                RequestStatusEnum.PAID: RequestStatus.PAID,
                RequestStatusEnum.COMPLETED: RequestStatus.COMPLETED
            }

            request.status = status_map[new_status]

            if new_status == RequestStatusEnum.REJECTED and rejection_reason:
                request.rejection_reason = rejection_reason

            db.commit()
            db.refresh(request)

            logger.info(f"Request status updated successfully: request_id={request_id}")
            return request

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update request status: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update request status"
            )

    @staticmethod
    def delete_request(request_id: int, citizen_id: int, db: Session):
        """Delete a request (only if status is SUBMITTED)"""
        logger.info(f"Deleting request_id={request_id} for citizen_id={citizen_id}")

        try:
            request = db.query(Request).filter(
                Request.request_id == request_id,
                Request.citizen_id == citizen_id
            ).first()

            if not request:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Request not found"
                )

            # Only allow deletion if status is SUBMITTED
            if request.status != RequestStatus.SUBMITTED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete request that is already under review or processed"
                )

            db.delete(request)
            db.commit()

            logger.info(f"Request deleted successfully: request_id={request_id}")
            return {"message": "Request deleted successfully"}

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete request: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete request"
            )


def notify_request_status_change(request_id: int, new_status: str, db: Session):
    from services.notification_service import NotificationService
    from schemas.notification import NotificationCreate

    request = db.query(Request).filter(Request.request_id == request_id).first()
    if request:
        notification = NotificationCreate(
            citizen_id=request.citizen_id,
            title=f"Request Status Update",
            message=f"Your request #{request_id} status has been updated to {new_status}",
            notification_type="REQUEST_UPDATE",
            request_id=request_id
        )
        NotificationService.create_notification(notification, db)

