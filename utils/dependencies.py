from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from models.account import Account
from utils.security import verify_token
from typing import Optional
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
) -> Account:
    """Get the current authenticated user"""
    token = credentials.credentials

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_token(token)
    if payload is None:
        logger.warning("Invalid token provided")
        raise credentials_exception

    email: str = payload.get("sub")
    user_id: int = payload.get("user_id")

    if email is None or user_id is None:
        logger.warning("Token missing required fields")
        raise credentials_exception

    user = db.query(Account).filter(Account.account_id == user_id).first()
    if user is None:
        logger.warning(f"User not found for id: {user_id}")
        raise credentials_exception

    if user.is_active != 1:
        logger.warning(f"Inactive user attempted access: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    logger.info(f"User authenticated: {email}")
    return user


