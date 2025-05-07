from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..dependencies import get_db, get_current_user
from ..models.task import Task
from ..models.user import User
from ..schemas.task import TaskCreate, TaskUpdate, TaskOut
from datetime import datetime

router = APIRouter()

@router.post("/tasks", response_model=TaskOut)
async def create_task(task: TaskCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    db_task = Task(**task.dict(), owner_id=current_user.id)
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task

@router.put("/tasks/{task_id}", response_model=TaskOut)
async def update_task(task_id: int, task: TaskUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    query = select(Task).filter(Task.id == task_id, Task.owner_id == current_user.id)
    result = await db.execute(query)
    db_task = result.scalars().first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    for key, value in task.dict(exclude_unset=True).items():
        setattr(db_task, key, value)
    await db.commit()
    await db.refresh(db_task)
    return db_task

@router.get("/tasks", response_model=List[TaskOut])
async def get_tasks(
    status: Optional[str] = None,
    priority: Optional[int] = None,
    created_at: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Task).filter(Task.owner_id == current_user.id)
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    if created_at:
        query = query.filter(Task.created_at >= created_at)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/tasks/search", response_model=List[TaskOut])
async def search_tasks(q: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    query = select(Task).filter(Task.owner_id == current_user.id).filter(
        (Task.title.contains(q)) | (Task.description.contains(q))
    )
    result = await db.execute(query)
    return result.scalars().all()