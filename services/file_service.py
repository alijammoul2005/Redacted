from sqlalchemy.orm import Session
from models.file_attachment import FileAttachment
from models.request import Request
from models.complaint import Complaint
from fastapi import HTTPException, status, UploadFile
from datetime import datetime
import os
import uuid
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class FileService:
    # Allowed file types
    ALLOWED_EXTENSIONS = {
        'pdf', 'jpg', 'jpeg', 'png', 'gif', 'doc', 'docx', 'txt'
    }

    ALLOWED_MIME_TYPES = {
        'application/pdf',
        'image/jpeg',
        'image/jpg',
        'image/png',
        'image/gif',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain'
    }

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

    UPLOAD_DIR = Path("uploads")

    @staticmethod
    def initialize_upload_directory():
        """Create upload directory if it doesn't exist"""
        FileService.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (FileService.UPLOAD_DIR / "requests").mkdir(exist_ok=True)
        (FileService.UPLOAD_DIR / "complaints").mkdir(exist_ok=True)

    @staticmethod
    def validate_file(file: UploadFile) -> bool:
        """Validate file type and size"""
        # Check file extension
        file_ext = file.filename.split('.')[-1].lower()
        if file_ext not in FileService.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {', '.join(FileService.ALLOWED_EXTENSIONS)}"
            )

        # Check MIME type
        if file.content_type not in FileService.ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File MIME type not allowed: {file.content_type}"
            )

        return True

    @staticmethod
    async def save_file(file: UploadFile, subdirectory: str) -> tuple:
        """Save uploaded file to disk"""
        try:
            # Generate unique filename
            file_ext = file.filename.split('.')[-1].lower()
            unique_filename = f"{uuid.uuid4()}.{file_ext}"

            # Create file path
            file_dir = FileService.UPLOAD_DIR / subdirectory
            file_dir.mkdir(parents=True, exist_ok=True)
            file_path = file_dir / unique_filename

            # Read and save file
            contents = await file.read()
            file_size = len(contents)

            # Check file size
            if file_size > FileService.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File too large. Maximum size: {FileService.MAX_FILE_SIZE / 1024 / 1024} MB"
                )

            # Write file
            with open(file_path, 'wb') as f:
                f.write(contents)

            logger.info(f"File saved: {file_path}")
            return str(file_path), file_size

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save file"
            )

    @staticmethod
    async def upload_request_file(
            file: UploadFile,
            request_id: int,
            citizen_id: int,
            db: Session
    ):
        """Upload file for a request"""
        logger.info(f"Uploading file for request_id: {request_id}")

        try:
            # Verify request exists and belongs to citizen
            request = db.query(Request).filter(
                Request.request_id == request_id,
                Request.citizen_id == citizen_id
            ).first()

            if not request:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Request not found or does not belong to you"
                )

            # Validate file
            FileService.validate_file(file)

            # Save file
            file_path, file_size = await FileService.save_file(file, "requests")

            # Create database record
            new_file = FileAttachment(
                filename=os.path.basename(file_path),
                original_filename=file.filename,
                file_path=file_path,
                file_size=file_size,
                file_type=file.content_type,
                uploaded_by=citizen_id,
                upload_date=datetime.utcnow(),
                request_id=request_id
            )

            db.add(new_file)
            db.commit()
            db.refresh(new_file)

            logger.info(f"File uploaded successfully: file_id={new_file.file_id}")
            return new_file

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error uploading file: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload file"
            )

    @staticmethod
    async def upload_complaint_file(
            file: UploadFile,
            complaint_id: int,
            citizen_id: int,
            db: Session
    ):
        """Upload file for a complaint"""
        logger.info(f"Uploading file for complaint_id: {complaint_id}")

        try:
            # Verify complaint exists and belongs to citizen
            complaint = db.query(Complaint).filter(
                Complaint.complaint_id == complaint_id,
                Complaint.citizen_id == citizen_id
            ).first()

            if not complaint:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Complaint not found or does not belong to you"
                )

            # Validate file
            FileService.validate_file(file)

            # Save file
            file_path, file_size = await FileService.save_file(file, "complaints")

            # Create database record
            new_file = FileAttachment(
                filename=os.path.basename(file_path),
                original_filename=file.filename,
                file_path=file_path,
                file_size=file_size,
                file_type=file.content_type,
                uploaded_by=citizen_id,
                upload_date=datetime.utcnow(),
                complaint_id=complaint_id
            )

            db.add(new_file)
            db.commit()
            db.refresh(new_file)

            logger.info(f"File uploaded successfully: file_id={new_file.file_id}")
            return new_file

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error uploading file: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload file"
            )

    @staticmethod
    def get_file_by_id(file_id: int, db: Session):
        """Get file metadata by ID"""
        file_record = db.query(FileAttachment).filter(
            FileAttachment.file_id == file_id
        ).first()

        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )

        return file_record

    @staticmethod
    def get_request_files(request_id: int, db: Session):
        """Get all files for a request"""
        files = db.query(FileAttachment).filter(
            FileAttachment.request_id == request_id
        ).all()

        return files

    @staticmethod
    def get_complaint_files(complaint_id: int, db: Session):
        """Get all files for a complaint"""
        files = db.query(FileAttachment).filter(
            FileAttachment.complaint_id == complaint_id
        ).all()

        return files

    @staticmethod
    def delete_file(file_id: int, citizen_id: int, db: Session):
        """Delete a file"""
        logger.info(f"Deleting file: file_id={file_id}")

        try:
            file_record = db.query(FileAttachment).filter(
                FileAttachment.file_id == file_id,
                FileAttachment.uploaded_by == citizen_id
            ).first()

            if not file_record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File not found or you don't have permission to delete it"
                )

            # Delete physical file
            if os.path.exists(file_record.file_path):
                os.remove(file_record.file_path)

            # Delete database record
            db.delete(file_record)
            db.commit()

            logger.info(f"File deleted successfully: file_id={file_id}")
            return {"message": "File deleted successfully"}

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting file: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete file"
            )
