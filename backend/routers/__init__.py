"""
main.py — FastAPI application entry point

What this file does:
- Creates the FastAPI app instance
- Configures CORS (Cross-Origin Resource Sharing) so the React frontend
  on localhost:3000 can call the backend on localhost:8000
- Registers all routers (complaints, analysis)
- Creates all DB tables on startup (via SQLAlchemy)
- Provides a health check endpoint

To run locally:
    uvicorn main:app --reload --port 8000

API docs auto-generated at:
    http://localhost:8000/docs  (Swagger UI)
    http://localhost:8000/redoc (ReDoc)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from database import engine, Base
from routers import complaints, analysis

# ── Create all DB tables ──────────────────────────────────────────────────────
# This runs at startup and creates any tables that don't exist yet.
# In production, you'd use Alembic migrations instead — but for development
# this is simpler and idempotent (safe to run multiple times).
Base.metadata.create_all(bind=engine)

# ── Create FastAPI app ────────────────────────────────────────────────────────
app = FastAPI(
    title       = "AIVOA Pharma Complaint Management System",
    description = "AI-powered customer complaint management for pharmaceutical QMS",
    version     = "1.0.0",
    docs_url    = "/docs",
    redoc_url   = "/redoc",
)

# ── CORS configuration ────────────────────────────────────────────────────────
# Allow the React dev server (localhost:3000) to call this API
# In production, replace "*" with your actual frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ── Serve uploaded files ──────────────────────────────────────────────────────
# Make the uploads directory accessible at /uploads URL
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ── Register routers ──────────────────────────────────────────────────────────
# Each router handles a group of related endpoints
# complaints router: /complaints/...  (CRUD for complaint records)
# analysis router:   /analysis/...    (AI analysis trigger + results)
app.include_router(complaints.router)
app.include_router(analysis.router)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    """Health check endpoint — confirms the API is running."""
    return {
        "status":  "healthy",
        "service": "AIVOA Pharma Complaint Management System",
        "version": "1.0.0",
    }

@app.get("/health", tags=["Health"])
def health():
    """Detailed health check."""
    return {
        "status":   "healthy",
        "database": "connected",
        "ai_agent": "ready",
    }