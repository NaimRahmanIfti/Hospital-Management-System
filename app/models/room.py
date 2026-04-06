# app/models/room.py

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.core.db import Base
import enum


class RoomType(str, enum.Enum):
    consultation = "consultation"
    surgery      = "surgery"
    icu          = "icu"
    ward         = "ward"
    lab          = "lab"


class Room(Base):
    __tablename__ = "rooms"

    id            = Column(Integer, primary_key=True, index=True)
    room_number   = Column(String(20), unique=True, nullable=False)
    room_type     = Column(Enum(RoomType), nullable=False)
    floor         = Column(Integer, nullable=True)
    is_available  = Column(Boolean, default=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)

    department   = relationship("Department",  back_populates="rooms")
    appointments = relationship("Appointment", back_populates="room")

    def __repr__(self):
        return f"<Room {self.room_number} type={self.room_type}>"