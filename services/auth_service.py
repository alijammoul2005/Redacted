from sqlalchemy.orm import Session
from models.account import Account
from models.citizen import Citizen
from models.employee import Employee
from schemas.auth import UserRegister, UserLogin, Token
from utils.security import verify_password, get_password_hash, create_access_token
from fastapi import HTTPException, status
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AuthService:

    @staticmethod
    def register_citizen(user_data: UserRegister, db: Session) -> Token:
        """Register a new citizen user"""
        logger.info(f"Registration attempt for email: {user_data.email}")

        # Check if email already exists
        existing_account = db.query(Account).filter(Account.email == user_data.email).first()
        if existing_account:
            logger.warning(f"Registration failed: Email already exists - {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Check if national ID already exists
        existing_citizen = db.query(Citizen).filter(
            Citizen.national_id == user_data.national_id
        ).first()
        if existing_citizen:
            logger.warning(f"Registration failed: National ID already exists - {user_data.national_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="National ID already registered"
            )

        try:
            # Create account
            new_account = Account(
                email=user_data.email,
                phone=user_data.phone,
                hashed_password=get_password_hash(user_data.password),
                created_at=datetime.utcnow(),
                is_active=1,
                failed_login_attempts=0
            )
            db.add(new_account)
            db.flush()  # Get the account_id

            # Create citizen profile
            new_citizen = Citizen(
                national_id=user_data.national_id,
                first_name=user_data.first_name,
                middle_name=user_data.middle_name,
                last_name=user_data.last_name,
                date_of_birth=user_data.date_of_birth,
                father_name=user_data.father_name,
                mother_name=user_data.mother_name,
                address=user_data.address,
                marital_status=user_data.marital_status,
                resident_status=True,
                account_id=new_account.account_id
            )
            db.add(new_citizen)
            db.commit()
            db.refresh(new_account)

            logger.info(f"User registered successfully: {user_data.email}")

            # Generate access token
            access_token = create_access_token(
                data={
                    "sub": new_account.email,
                    "user_id": new_account.account_id,
                    "role": "citizen"
                }
            )

            return Token(
                access_token=access_token,
                token_type="bearer",
                user_id=new_account.account_id,
                email=new_account.email,
                role="citizen"
            )

        except Exception as e:
            db.rollback()
            logger.error(f"Registration failed: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration failed"
            )

    @staticmethod
    def login(login_data: UserLogin, db: Session) -> Token:
        """Authenticate a user and return a token"""
        logger.info(f"Login attempt for email: {login_data.email}")

        # Find account
        account = db.query(Account).filter(Account.email == login_data.email).first()

        if not account:
            logger.warning(f"Login failed: Account not found - {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )

        # Check if account is locked
        if account.locked_until and account.locked_until > datetime.utcnow():
            logger.warning(f"Login failed: Account locked - {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account is locked until {account.locked_until}"
            )

        # Verify password
        if not verify_password(login_data.password, account.hashed_password):
            # Increment failed attempts
            account.failed_login_attempts += 1

            # Lock account after 5 failed attempts
            if account.failed_login_attempts >= 5:
                account.locked_until = datetime.utcnow() + timedelta(minutes=30)
                logger.warning(f"Account locked due to failed attempts: {login_data.email}")

            db.commit()

            logger.warning(f"Login failed: Invalid password - {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )

        # Check if account is active
        if account.is_active != 1:
            logger.warning(f"Login failed: Account inactive - {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive"
            )

        # Reset failed attempts on successful login
        account.failed_login_attempts = 0
        account.locked_until = None
        db.commit()

        # Determine role (citizen or employee)
        role = "citizen"
        if db.query(Employee).filter(Employee.account_id == account.account_id).first():
            role = "employee"

        logger.info(f"Login successful: {login_data.email} as {role}")

        # Generate access token
        access_token = create_access_token(
            data={
                "sub": account.email,
                "user_id": account.account_id,
                "role": role
            }
        )

        return Token(
            access_token=access_token,
            token_type="bearer",
            user_id=account.account_id,
            email=account.email,
            role=role
        )

