from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "pending"
    priority: int

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[int] = None

class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: str
    priority: int
    created_at: datetime
    owner_id: int
    class Config:
        orm_mode = True