"""
Consilo SaaS - Multi-tenant FastAPI Backend
Week 1 Production Version

Architecture:
- Multi-tenant isolation via X-Tenant-ID header
- Encrypted Jira credentials per tenant
- Usage tracking for billing
- Analysis history storage
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from .database import engine, Base
from .routes import analyze, tenants, health

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Consilo API",
    description="AI-powered delivery risk intelligence for engineering teams",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware (configure for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict to frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(tenants.router, prefix="/api/tenants", tags=["Tenants"])
app.include_router(analyze.router, prefix="/api/analyze", tags=["Analysis"])

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )

@app.get("/")
def root():
    return {
        "name": "Consilo API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)
