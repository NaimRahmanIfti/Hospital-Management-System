# main.py

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.db import Base
import app.models  # noqa - registers all models

from app.routers import auth, users, patients, doctors, appointments, medical_records, invoices

# ── Database ──────────────────────────────────────────────────────
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./hms_dev.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Patch the global db module so all routers use this engine
import app.core.db as _db
_db.engine = engine
_db.SessionLocal = SessionLocal

Base.metadata.create_all(bind=engine)

# ── App ───────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    debug=True,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(patients.router)
app.include_router(doctors.router)
app.include_router(appointments.router)
app.include_router(medical_records.router)
app.include_router(invoices.router)

@app.get("/", tags=["System"])
def root():
    return {"app": settings.APP_NAME, "version": "1.0.0", "docs": "/docs"}

@app.get("/health", tags=["System"])
def health():
    return {"status": "ok"}