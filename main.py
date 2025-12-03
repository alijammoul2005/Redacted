from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from database import engine, Base
from routers import auth, citizens, employees, requests, payments, feedback, public
from logging_config import setup_logging
import logging
import time
from routers import auth, citizens, employees, requests, payments, feedback, complaints, files, announcements, notifications
import os

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Create database tables
try:
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Failed to create database tables: {str(e)}", exc_info=True)
    raise

app = FastAPI(
    title="Municipality Management System API",
    description="Backend API for Municipality Management System",
    version="1.0.0"
)

# CORS configuration for Flutter app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    # Log request
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    logger.debug(f"Request headers: {request.headers}")

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        # Log response
        logger.info(
            f"Request completed: {request.method} {request.url.path} "
            f"- Status: {response.status_code} - Time: {process_time:.3f}s"
        )

        response.headers["X-Process-Time"] = str(process_time)
        return response

    except Exception as e:
        logger.error(
            f"Request failed: {request.method} {request.url.path} - Error: {str(e)}",
            exc_info=True
        )
        raise


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}: {str(exc)}",
        exc_info=True
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "path": str(request.url.path),
            "method": request.method
        }
    )


# Include routers
logger.info("Registering routers...")
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(citizens.router, prefix="/api/citizens", tags=["Citizens"])
app.include_router(employees.router, prefix="/api/employees", tags=["Employees"])
app.include_router(requests.router, prefix="/api/requests", tags=["Requests"])
app.include_router(payments.router, prefix="/api/payments", tags=["Payments"])
app.include_router(feedback.router, prefix="/api/feedback", tags=["Feedback"])
app.include_router(files.router, prefix="/api/files", tags=["Files"])
app.include_router(public.router, prefix="/api/public", tags=["Public/Homepage"])
app.include_router(announcements.router, prefix="/api/announcements", tags=["Announcements"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
logger.info("Routers registered successfully")


@app.on_event("startup")
async def startup_event():
    logger.info("=" * 50)
    logger.info("Municipality Management System API Starting...")
    logger.info("=" * 50)


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("=" * 50)
    logger.info("Municipality Management System API Shutting Down...")
    logger.info("=" * 50)


@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {
        "message": "Municipality Management System API",
        "version": "1.0.0",
        "status": "running"
    }
app.include_router(complaints.router, prefix="/api/complaints", tags=["Complaints"])
app.include_router(feedback.router, prefix="/api/feedbacks", tags=["Feedbacks"])

# Mount static files for frontend
frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/frontend", StaticFiles(directory=frontend_dir), name="frontend")
    logger.info(f"Frontend static files mounted at /frontend from {frontend_dir}")

    # Serve index.html at root path
    @app.get("/index.html")
    async def serve_index():
        index_path = os.path.join(frontend_dir, "index.html")
        return FileResponse(index_path)
else:
    logger.warning(f"Frontend directory not found at {frontend_dir}")


@app.get("/health")
async def health_check():
    logger.debug("Health check endpoint accessed")
    try:
        # Test database connection
        from sqlalchemy import text
        from database import SessionLocal
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("Health check passed - Database connection OK")
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }
        )

