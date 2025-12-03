from sqlalchemy.orm import Session
from models.complaint import Complaint, ComplaintResponse, ComplaintStatus, ComplaintCategory
from models.citizen import Citizen
from models.employee import Employee
from schemas.complaint import ComplaintCreate, ComplaintUpdate, ComplaintResponseCreate, ComplaintStatusEnum, ComplaintCategoryEnum
from fastapi import HTTPException, status
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ComplaintService:

    @staticmethod
    def create_complaint(complaint_data: ComplaintCreate, citizen_id: int, db: Session):
        """Create a new complaint"""
        logger.info(f"Creating complaint for citizen_id: {citizen_id}")

        try:
            # Map schema enum to model enum
            category_map = {
                ComplaintCategoryEnum.INFRASTRUCTURE: ComplaintCategory.INFRASTRUCTURE,
                ComplaintCategoryEnum.SANITATION: ComplaintCategory.SANITATION,
                ComplaintCategoryEnum.WATER_SUPPLY: ComplaintCategory.WATER_SUPPLY,
                ComplaintCategoryEnum.ELECTRICITY: ComplaintCategory.ELECTRICITY,
                ComplaintCategoryEnum.ROAD_DAMAGE: ComplaintCategory.ROAD_DAMAGE,
                ComplaintCategoryEnum.GARBAGE_COLLECTION: ComplaintCategory.GARBAGE_COLLECTION,
                ComplaintCategoryEnum.NOISE_POLLUTION: ComplaintCategory.NOISE_POLLUTION,
                ComplaintCategoryEnum.ILLEGAL_CONSTRUCTION: ComplaintCategory.ILLEGAL_CONSTRUCTION,
                ComplaintCategoryEnum.OTHER: ComplaintCategory.OTHER
            }

            new_complaint = Complaint(
                citizen_id=citizen_id,
                category=category_map[complaint_data.category],
                title=complaint_data.title,
                description=complaint_data.description,
                location=complaint_data.location,
                status=ComplaintStatus.SUBMITTED,
                submission_date=datetime.utcnow()
            )

            db.add(new_complaint)
            db.commit()
            db.refresh(new_complaint)

            logger.info(f"Complaint created: complaint_id={new_complaint.complaint_id}")
            return new_complaint

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create complaint: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create complaint"
            )

    @staticmethod
    def get_citizen_complaints(citizen_id: int, db: Session):
        """Get all complaints for a citizen"""
        logger.info(f"Fetching complaints for citizen_id: {citizen_id}")

        try:
            complaints = db.query(Complaint).filter(
                Complaint.citizen_id == citizen_id
            ).order_by(Complaint.submission_date.desc()).all()

            logger.info(f"Found {len(complaints)} complaints")
            return complaints

        except Exception as e:
            logger.error(f"Failed to fetch complaints: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch complaints"
            )

    @staticmethod
    def get_complaint_by_id(complaint_id: int, db: Session):
        """Get complaint details with responses"""
        logger.info(f"Fetching complaint: complaint_id={complaint_id}")

        try:
            complaint = db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()

            if not complaint:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Complaint not found"
                )

            # Get citizen info
            citizen = db.query(Citizen).filter(Citizen.citizen_id == complaint.citizen_id).first()
            citizen_name = f"{citizen.first_name} {citizen.last_name}" if citizen else "Unknown"

            # Get employee info if assigned
            employee_name = None
            if complaint.assigned_employee_id:
                employee = db.query(Employee).filter(
                    Employee.employee_id == complaint.assigned_employee_id
                ).first()
                if employee:
                    emp_citizen = db.query(Citizen).filter(
                        Citizen.citizen_id == employee.citizen_id
                    ).first()
                    employee_name = f"{emp_citizen.first_name} {emp_citizen.last_name}" if emp_citizen else "Unknown"

            # Get responses
            responses = db.query(ComplaintResponse).filter(
                ComplaintResponse.complaint_id == complaint_id
            ).order_by(ComplaintResponse.response_date.asc()).all()

            response_details = []
            for resp in responses:
                emp = db.query(Employee).filter(Employee.employee_id == resp.employee_id).first()
                if emp:
                    emp_cit = db.query(Citizen).filter(Citizen.citizen_id == emp.citizen_id).first()
                    emp_name = f"{emp_cit.first_name} {emp_cit.last_name}" if emp_cit else "Unknown"
                else:
                    emp_name = "Unknown"

                response_details.append({
                    "response_id": resp.response_id,
                    "employee_name": emp_name,
                    "message": resp.message,
                    "response_date": resp.response_date
                })

            result = {
                "complaint_id": complaint.complaint_id,
                "citizen_id": complaint.citizen_id,
                "citizen_name": citizen_name,
                "category": complaint.category.value,
                "title": complaint.title,
                "description": complaint.description,
                "location": complaint.location,
                "status": complaint.status.value,
                "submission_date": complaint.submission_date,
                "assigned_employee_id": complaint.assigned_employee_id,
                "assigned_employee_name": employee_name,
                "resolution_notes": complaint.resolution_notes,
                "resolved_date": complaint.resolved_date,
                "responses": response_details
            }

            return result

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to fetch complaint: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch complaint"
            )

    @staticmethod
    def get_all_complaints(db: Session, status_filter: str = None, category_filter: str = None, skip: int = 0,
                           limit: int = 100):
        """Get all complaints (for employees)"""
        logger.info(f"Fetching all complaints")

        try:
            query = db.query(Complaint)

            if status_filter:
                try:
                    status_enum = ComplaintStatus[status_filter.upper()]
                    query = query.filter(Complaint.status == status_enum)
                except KeyError:
                    logger.warning(f"Invalid status filter: {status_filter}")

            if category_filter:
                query = query.filter(Complaint.category.like(f"%{category_filter}%"))

            complaints = query.order_by(Complaint.submission_date.desc()).offset(skip).limit(limit).all()

            logger.info(f"Found {len(complaints)} complaints")
            return complaints

        except Exception as e:
            logger.error(f"Failed to fetch complaints: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch complaints"
            )

    @staticmethod
    def assign_complaint(complaint_id: int, employee_id: int, db: Session):
        """Assign complaint to employee"""
        logger.info(f"Assigning complaint {complaint_id} to employee {employee_id}")

        try:
            complaint = db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()

            if not complaint:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Complaint not found"
                )

            employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
            if not employee:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Employee not found"
                )

            complaint.assigned_employee_id = employee_id
            complaint.status = ComplaintStatus.UNDER_REVIEW

            db.commit()
            db.refresh(complaint)

            logger.info(f"Complaint assigned successfully")
            return complaint

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to assign complaint: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to assign complaint"
            )

    @staticmethod
    def update_complaint_status(complaint_id: int, update_data: ComplaintUpdate, db: Session):
        """Update complaint status"""
        logger.info(f"Updating complaint {complaint_id}")

        try:
            complaint = db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()

            if not complaint:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Complaint not found"
                )

            if update_data.status:
                status_map = {
                    ComplaintStatusEnum.SUBMITTED: ComplaintStatus.SUBMITTED,
                    ComplaintStatusEnum.UNDER_REVIEW: ComplaintStatus.UNDER_REVIEW,
                    ComplaintStatusEnum.IN_PROGRESS: ComplaintStatus.IN_PROGRESS,
                    ComplaintStatusEnum.RESOLVED: ComplaintStatus.RESOLVED,
                    ComplaintStatusEnum.CLOSED: ComplaintStatus.CLOSED,
                    ComplaintStatusEnum.REJECTED: ComplaintStatus.REJECTED
                }
                complaint.status = status_map[update_data.status]

                if update_data.status == ComplaintStatusEnum.RESOLVED:
                    complaint.resolved_date = datetime.utcnow()

            if update_data.assigned_employee_id is not None:
                complaint.assigned_employee_id = update_data.assigned_employee_id

            if update_data.resolution_notes:
                complaint.resolution_notes = update_data.resolution_notes

            db.commit()
            db.refresh(complaint)

            logger.info(f"Complaint updated successfully")
            return complaint

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update complaint: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update complaint"
            )

    @staticmethod
    def add_response(complaint_id: int, employee_id: int, response_data: ComplaintResponseCreate, db: Session):
        """Add employee response to complaint"""
        logger.info(f"Adding response to complaint {complaint_id}")

        try:
            complaint = db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()

            if not complaint:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Complaint not found"
                )

            new_response = ComplaintResponse(
                complaint_id=complaint_id,
                employee_id=employee_id,
                message=response_data.message,
                response_date=datetime.utcnow()
            )

            db.add(new_response)
            db.commit()
            db.refresh(new_response)

            logger.info(f"Response added successfully")
            return new_response

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to add response: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add response"
            )

    @staticmethod
    def delete_complaint(complaint_id: int, citizen_id: int, db: Session):
        """Delete complaint (only if SUBMITTED)"""
        logger.info(f"Deleting complaint {complaint_id}")

        try:
            complaint = db.query(Complaint).filter(
                Complaint.complaint_id == complaint_id,
                Complaint.citizen_id == citizen_id
            ).first()

            if not complaint:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Complaint not found"
                )

            if complaint.status != ComplaintStatus.SUBMITTED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete complaint that is already being processed"
                )

            db.delete(complaint)
            db.commit()

            logger.info(f"Complaint deleted successfully")
            return {"message": "Complaint deleted successfully"}

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete complaint: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete complaint"
            )
