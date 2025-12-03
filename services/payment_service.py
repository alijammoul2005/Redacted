from sqlalchemy.orm import Session
from models.payment import Payment, PaymentStatus
from models.request import Request, RequestStatus
from models.citizen import Citizen
from schemas.payment import PaymentCreate, PaymentStatusEnum
from fastapi import HTTPException, status
from datetime import datetime
import logging
import random
import string

logger = logging.getLogger(__name__)


class PaymentService:
    # Fee structure for different document types
    FEE_STRUCTURE = {
        "Building Permit": 500.00,
        "Business License": 300.00,
        "Birth Certificate": 50.00,
        "Marriage Certificate": 75.00,
        "Residency Certificate": 40.00,
        "Tax Clearance": 100.00,
        "Land Registry": 1000.00,
        "Other": 100.00
    }

    @staticmethod
    def calculate_fee(request_type: str) -> float:
        """Calculate fee based on request type"""
        return PaymentService.FEE_STRUCTURE.get(request_type, 100.00)

    @staticmethod
    def generate_transaction_id() -> str:
        """Generate a unique transaction ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"TXN-{timestamp}-{random_str}"

    @staticmethod
    def generate_receipt_number() -> str:
        """Generate a unique receipt number"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_str = ''.join(random.choices(string.digits, k=4))
        return f"RCP-{timestamp}-{random_str}"

    @staticmethod
    def simulate_payment_gateway(payment_data: PaymentCreate) -> dict:
        """
        Simulate payment gateway processing
        In production, this would integrate with real payment providers
        """
        # Simulate payment processing delay
        import time
        time.sleep(1)

        # Simulate 90% success rate
        success = random.random() < 0.9

        if success:
            return {
                "status": "success",
                "transaction_id": PaymentService.generate_transaction_id(),
                "message": "Payment processed successfully"
            }
        else:
            return {
                "status": "failed",
                "transaction_id": None,
                "message": "Payment declined by bank"
            }

    @staticmethod
    def create_payment(payment_data: PaymentCreate, citizen_id: int, db: Session):
        """Create and process a payment"""
        logger.info(f"Payment creation for request_id: {payment_data.request_id}")

        try:
            # Check if request exists and belongs to citizen
            request = db.query(Request).filter(Request.request_id == payment_data.request_id).first()

            if not request:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Request not found"
                )

            if request.citizen_id != citizen_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only pay for your own requests"
                )

            # Check if request is approved
            if request.status != RequestStatus.APPROVED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Request must be approved before payment"
                )

            # Check if payment already exists
            existing_payment = db.query(Payment).filter(
                Payment.request_id == payment_data.request_id
            ).first()

            if existing_payment:
                if existing_payment.status == PaymentStatus.COMPLETED:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Payment already completed for this request"
                    )

                # Check retry count
                if existing_payment.retry_count >= 3:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Maximum payment attempts (3) exceeded. Please contact support."
                    )

                # Increment retry count
                existing_payment.retry_count += 1
                payment = existing_payment
            else:
                # Calculate amount
                amount = PaymentService.calculate_fee(request.request_type)

                # Create new payment record
                payment = Payment(
                    request_id=payment_data.request_id,
                    amount=amount,
                    payment_date=datetime.utcnow(),
                    status=PaymentStatus.PENDING,
                    payment_method=payment_data.payment_method.value,
                    retry_count=0
                )
                db.add(payment)
                db.flush()

            # Update status to PROCESSING
            payment.status = PaymentStatus.PROCESSING
            db.commit()

            # Process payment through gateway
            logger.info(f"Processing payment for request_id: {payment_data.request_id}")
            gateway_response = PaymentService.simulate_payment_gateway(payment_data)

            if gateway_response["status"] == "success":
                # Payment successful
                payment.status = PaymentStatus.COMPLETED
                payment.transaction_id = gateway_response["transaction_id"]
                payment.payment_date = datetime.utcnow()

                # Update request status to PAID
                request.status = RequestStatus.PAID

                logger.info(f"Payment successful: transaction_id={gateway_response['transaction_id']}")
            else:
                # Payment failed
                payment.status = PaymentStatus.FAILED
                logger.warning(f"Payment failed: {gateway_response['message']}")

            db.commit()
            db.refresh(payment)

            return payment

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Payment processing error: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Payment processing failed"
            )

    @staticmethod
    def get_payment_by_id(payment_id: int, db: Session):
        """Get payment details by ID"""
        logger.info(f"Fetching payment: payment_id={payment_id}")

        try:
            payment = db.query(Payment).filter(Payment.payment_id == payment_id).first()

            if not payment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Payment not found"
                )

            # Get request and citizen details
            request = db.query(Request).filter(Request.request_id == payment.request_id).first()
            citizen = db.query(Citizen).filter(Citizen.citizen_id == request.citizen_id).first()

            citizen_name = f"{citizen.first_name} {citizen.last_name}" if citizen else "Unknown"

            return {
                "payment_id": payment.payment_id,
                "request_id": payment.request_id,
                "request_type": request.request_type,
                "citizen_name": citizen_name,
                "amount": payment.amount,
                "payment_date": payment.payment_date,
                "status": payment.status.value,
                "transaction_id": payment.transaction_id,
                "payment_method": payment.payment_method,
                "retry_count": payment.retry_count
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to fetch payment: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch payment details"
            )

    @staticmethod
    def get_payment_by_request(request_id: int, db: Session):
        """Get payment for a specific request"""
        payment = db.query(Payment).filter(Payment.request_id == request_id).first()
        return payment

    @staticmethod
    def get_citizen_payments(citizen_id: int, db: Session):
        """Get all payments for a citizen"""
        logger.info(f"Fetching payments for citizen_id: {citizen_id}")

        try:
            # Get all requests for the citizen
            requests = db.query(Request).filter(Request.citizen_id == citizen_id).all()
            request_ids = [req.request_id for req in requests]

            # Get payments for these requests
            payments = db.query(Payment).filter(Payment.request_id.in_(request_ids)).all()

            result = []
            for payment in payments:
                request = db.query(Request).filter(Request.request_id == payment.request_id).first()
                citizen = db.query(Citizen).filter(Citizen.citizen_id == citizen_id).first()

                citizen_name = f"{citizen.first_name} {citizen.last_name}" if citizen else "Unknown"

                result.append({
                    "payment_id": payment.payment_id,
                    "request_id": payment.request_id,
                    "request_type": request.request_type,
                    "citizen_name": citizen_name,
                    "amount": payment.amount,
                    "payment_date": payment.payment_date,
                    "status": payment.status.value,
                    "transaction_id": payment.transaction_id,
                    "payment_method": payment.payment_method,
                    "retry_count": payment.retry_count
                })

            logger.info(f"Found {len(result)} payments for citizen_id: {citizen_id}")
            return result

        except Exception as e:
            logger.error(f"Failed to fetch citizen payments: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch payment history"
            )

    @staticmethod
    def get_payment_receipt(payment_id: int, citizen_id: int, db: Session):
        """Generate payment receipt"""
        logger.info(f"Generating receipt for payment_id: {payment_id}")

        try:
            payment = db.query(Payment).filter(Payment.payment_id == payment_id).first()

            if not payment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Payment not found"
                )

            # Verify payment belongs to citizen
            request = db.query(Request).filter(Request.request_id == payment.request_id).first()
            if request.citizen_id != citizen_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only view your own payment receipts"
                )

            # Only generate receipt for completed payments
            if payment.status != PaymentStatus.COMPLETED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Receipt only available for completed payments"
                )

            citizen = db.query(Citizen).filter(Citizen.citizen_id == citizen_id).first()
            citizen_name = f"{citizen.first_name} {citizen.last_name}" if citizen else "Unknown"

            receipt = {
                "payment_id": payment.payment_id,
                "transaction_id": payment.transaction_id,
                "request_id": payment.request_id,
                "request_type": request.request_type,
                "citizen_name": citizen_name,
                "amount": payment.amount,
                "payment_date": payment.payment_date,
                "payment_method": payment.payment_method,
                "receipt_number": PaymentService.generate_receipt_number(),
                "municipality_info": {
                    "name": "Municipality Management System",
                    "address": "Beirut, Lebanon",
                    "phone": "+961 1 234567",
                    "email": "info@municipality.gov.lb"
                }
            }

            logger.info(f"Receipt generated: payment_id={payment_id}")
            return receipt

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to generate receipt: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate receipt"
            )

    @staticmethod
    def get_all_payments(db: Session, status_filter: str = None, skip: int = 0, limit: int = 100):
        """Get all payments (for employees/admins)"""
        logger.info(f"Fetching all payments with filter: {status_filter}")

        try:
            query = db.query(Payment)

            if status_filter:
                try:
                    status_enum = PaymentStatus[status_filter.upper()]
                    query = query.filter(Payment.status == status_enum)
                except KeyError:
                    logger.warning(f"Invalid status filter: {status_filter}")

            payments = query.order_by(Payment.payment_date.desc()).offset(skip).limit(limit).all()

            result = []
            for payment in payments:
                request = db.query(Request).filter(Request.request_id == payment.request_id).first()
                citizen = db.query(Citizen).filter(Citizen.citizen_id == request.citizen_id).first()

                citizen_name = f"{citizen.first_name} {citizen.last_name}" if citizen else "Unknown"

                result.append({
                    "payment_id": payment.payment_id,
                    "request_id": payment.request_id,
                    "request_type": request.request_type,
                    "citizen_name": citizen_name,
                    "amount": payment.amount,
                    "payment_date": payment.payment_date,
                    "status": payment.status.value,
                    "transaction_id": payment.transaction_id,
                    "payment_method": payment.payment_method,
                    "retry_count": payment.retry_count
                })

            logger.info(f"Found {len(result)} payments")
            return result

        except Exception as e:
            logger.error(f"Failed to fetch all payments: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch payments"
            )

    @staticmethod
    def get_fee_structure():
        """Get the fee structure for all document types"""
        return PaymentService.FEE_STRUCTURE


def notify_payment_success(payment_id: int, db: Session):
    from services.notification_service import NotificationService
    from schemas.notification import NotificationCreate

    payment = db.query(Payment).filter(Payment.payment_id == payment_id).first()
    if payment:
        request = db.query(Request).filter(Request.request_id == payment.request_id).first()
        notification = NotificationCreate(
            citizen_id=request.citizen_id,
            title="Payment Successful",
            message=f"Your payment of ${payment.amount} has been received successfully.",
            notification_type="PAYMENT_REMINDER",
            request_id=payment.request_id
        )
        NotificationService.create_notification(notification, db)
