# app/core/db.py

from sqlalchemy import create_engine
# sessionmaker creates a "factory" — a blueprint for making DB sessions
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings


# ── 1. ENGINE ────────────────────────────────────────────────────────────────
#
# The engine is SQLAlchemy's core — it holds the actual connection pool
# to your database. Think of it like this:
#
#   Engine = the phone line to PostgreSQL
#   Session = one phone call on that line
#
# create_engine() does NOT open a connection immediately.
# It just configures HOW to connect when needed.
#
# echo=settings.DEBUG → when True, every SQL statement gets printed.
# Example output you'll see in your terminal:
#   SELECT users.id, users.email FROM users WHERE users.id = 1
# This teaches you what SQLAlchemy is actually doing behind the scenes.
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=False,
)

# ── 2. SESSION FACTORY ───────────────────────────────────────────────────────
#
# SessionLocal is NOT a session — it's a factory that creates sessions.
# Every API request gets its OWN session (its own conversation with the DB).
# This is important: sessions should never be shared between requests.
#
# autocommit=False → you must explicitly call db.commit() to save changes.
#   Why? So you can group multiple changes and roll them all back if one fails.
#   Example: creating a patient AND their invoice — if the invoice fails,
#   you want to undo the patient creation too. That's a "transaction".
#
# autoflush=False → SQLAlchemy won't auto-send pending changes to the DB.
#   This gives you more control over when things get written.
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


# ── 3. BASE CLASS ────────────────────────────────────────────────────────────
#
# Every database model (User, Patient, Doctor, Appointment...)
# will inherit from this Base class.
#
# SQLAlchemy uses Base to keep a "registry" of all your models.
# When you call Base.metadata.create_all(engine), it looks at every
# class registered with this Base and creates the corresponding SQL tables.
#
# Why DeclarativeBase instead of the old declarative_base()?
# SQLAlchemy 2.0+ uses DeclarativeBase — it has better type hints
# and integrates cleaner with Pydantic.
class Base(DeclarativeBase):
    pass


# ── 4. DEPENDENCY FUNCTION ───────────────────────────────────────────────────
#
# This function is a FastAPI "dependency". When you write:
#   def get_patients(db: Session = Depends(get_db)):
# FastAPI calls get_db() automatically before your function runs,
# and passes the session as 'db'.
#
# 'yield' makes this a generator function:
#   - Code BEFORE yield runs at the START of the request (creates session)
#   - The yielded value is injected into your route function
#   - Code AFTER yield (in finally) runs at the END of the request
#
# 'finally' guarantees db.close() runs EVEN IF the request threw an error.
# Without this, you'd leak database connections and eventually crash.
def get_db():
    db = SessionLocal()   # Open a new session for this request
    try:
        yield db          # Hand the session to the route function
    finally:
        db.close()        # Always close — runs after the response is sent