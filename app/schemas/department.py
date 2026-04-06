# app/schemas/department.py

from pydantic import BaseModel, Field
from typing import Optional


class DepartmentBase(BaseModel):
    name:        str           = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    location:    Optional[str] = None


class DepartmentCreate(DepartmentBase):
    pass   # inherits everything from Base — nothing extra needed on create


class DepartmentUpdate(BaseModel):
    name:        Optional[str] = None
    description: Optional[str] = None
    location:    Optional[str] = None


class DepartmentResponse(DepartmentBase):
    id: int
    model_config = {"from_attributes": True}