from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from database import get_db
from schemas.auth import UserRegister, UserLogin, Token
from services.auth_service import AuthService
from utils.dependencies import get_current_user
from models.account import Account
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new citizen user

    - **email**: Valid email address
    - **password**: Minimum 8 characters
    - **national_id**: Unique national identification number
    - **first_name**: First name
    - **last_name**: Last name
    - **date_of_birth**: Date of birth in YYYY-MM-DD format
    """
    return AuthService.register_citizen(user_data, db)


@router.post("/login", response_model=Token)
async def login(request: Request, login_data: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate a user and receive an access token

    - **email**: Your registered email
    - **password**: Your password

    Returns an access token that should be included in subsequent requests
    """
    # Debug logging
    body = await request.body()
    logger.info(f"Login request body: {body.decode()}")
    logger.info(f"Login data parsed: email={login_data.email}")
    return AuthService.login(login_data, db)


@router.get("/me")
async def get_current_user_info(current_user: Account = Depends(get_current_user)):
    """
    Get information about the currently authenticated user

    Requires: Valid JWT token in Authorization header
    """
    logger.info(f"User info requested: {current_user.email}")
    return {
        "account_id": current_user.account_id,
        "email": current_user.email,
        "phone": current_user.phone,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at
    }


@router.post("/logout")
async def logout(current_user: Account = Depends(get_current_user)):
    """
    Logout the current user (client should delete the token)

    Requires: Valid JWT token in Authorization header
    """
    logger.info(f"User logged out: {current_user.email}")
    return {"message": "Successfully logged out"}


@router.get("/test")
async def test_auth():
    """Test endpoint to verify auth router is working"""
    logger.info("Auth test endpoint called")
    return {"message": "Auth router working"}
