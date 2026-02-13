"""
Health check endpoint
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "service": "Consilo API",
        "version": "1.0.0"
    }
