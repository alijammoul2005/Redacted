from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import get_db
from schemas.file_attachment import FileAttachmentResponse, FileUploadResponse
from services.file_service import FileService
from utils.dependencies import get_current_user
from models.account import Account
from models.citizen import Citizen
from models.employee import Employee
from typing import List
import logging
import os

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize upload directory on startup
FileService.initialize_upload_directory()


# ============================================
# REQUEST FILE ENDPOINTS
# ============================================

@router.post("/requests/{request_id}/upload", response_model=FileUploadResponse)
async def upload_request_file(
        request_id: int,
        file: UploadFile = File(...),
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Upload a file attachment to a request (Citizens only)

    Allowed file types: PDF, JPG, JPEG, PNG, GIF, DOC, DOCX, TXT
    Maximum file size: 10 MB
    """
    logger.info(f"File upload for request {request_id} by user: {current_user.email}")

    citizen = db.query(Citizen).filter(Citizen.account_id == current_user.account_id).first()

    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only citizens can upload files"
        )

    uploaded_file = await FileService.upload_request_file(file, request_id, citizen.citizen_id, db)

    return FileUploadResponse(
        file_id=uploaded_file.file_id,
        filename=uploaded_file.filename,
        original_filename=uploaded_file.original_filename,
        file_size=uploaded_file.file_size,
        file_type=uploaded_file.file_type,
        message="File uploaded successfully"
    )


@router.get("/requests/{request_id}/files", response_model=List[FileAttachmentResponse])
async def get_request_files(
        request_id: int,
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get all file attachments for a request
    """
    return FileService.get_request_files(request_id, db)


# ============================================
# COMPLAINT FILE ENDPOINTS
# ============================================

@router.post("/complaints/{complaint_id}/upload", response_model=FileUploadResponse)
async def upload_complaint_file(
        complaint_id: int,
        file: UploadFile = File(...),
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Upload a file/photo to a complaint (Citizens only)

    Allowed file types: PDF, JPG, JPEG, PNG, GIF, DOC, DOCX, TXT
    Maximum file size: 10 MB
    """
    logger.info(f"File upload for complaint {complaint_id} by user: {current_user.email}")

    citizen = db.query(Citizen).filter(Citizen.account_id == current_user.account_id).first()

    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only citizens can upload files"
        )

    uploaded_file = await FileService.upload_complaint_file(file, complaint_id, citizen.citizen_id, db)

    return FileUploadResponse(
        file_id=uploaded_file.file_id,
        filename=uploaded_file.filename,
        original_filename=uploaded_file.original_filename,
        file_size=uploaded_file.file_size,
        file_type=uploaded_file.file_type,
        message="File uploaded successfully"
    )


@router.get("/complaints/{complaint_id}/files", response_model=List[FileAttachmentResponse])
async def get_complaint_files(
        complaint_id: int,
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get all file attachments for a complaint
    """
    return FileService.get_complaint_files(complaint_id, db)


# ============================================
# FILE MANAGEMENT ENDPOINTS
# ============================================

@router.get("/{file_id}", response_model=FileAttachmentResponse)
async def get_file_metadata(
        file_id: int,
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get file metadata by ID
    """
    return FileService.get_file_by_id(file_id, db)


@router.get("/{file_id}/download")
async def download_file(
        file_id: int,
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Download a file by ID
    """
    file_record = FileService.get_file_by_id(file_id, db)

    # Check if file exists on disk
    if not os.path.exists(file_record.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server"
        )

    # Return file for download
    return FileResponse(
        path=file_record.file_path,
        filename=file_record.original_filename,
        media_type=file_record.file_type
    )


@router.delete("/{file_id}")
async def delete_file(
        file_id: int,
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Delete a file (only the uploader can delete)
    """
    citizen = db.query(Citizen).filter(Citizen.account_id == current_user.account_id).first()

    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only citizens can delete files"
        )

    return FileService.delete_file(file_id, citizen.citizen_id, db)
