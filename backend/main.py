import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import Base, engine
from routers import analysis, complaints

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AIVOA Pharma Complaint Management System",
    description="AI-powered customer complaint management for pharmaceutical QMS",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("uploads", exist_ok=True)

app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads",
)

app.include_router(complaints.router)
app.include_router(analysis.router)


@app.get("/", tags=["Health"])
def root():
    return {
        "status": "healthy",
        "service": "AIVOA Pharma Complaint Management System",
        "version": "1.0.0",
    }


@app.get("/health", tags=["Health"])
def health():
    return {
        "status": "healthy",
        "database": "connected",
        "ai_agent": "ready",
    }