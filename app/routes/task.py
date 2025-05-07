from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..dependencies import get_db, get_current_user
from ..models.task import Task
from ..models.user import User
from ..schemas.task import TaskCreate, TaskUpdate, TaskOut
from datetime import datetime
from fastapi.responses import JSONResponse

router = APIRouter(tags=["Tasks"], prefix="/tasks")

@router.post(
    "",
    response_model=TaskOut,
    summary="Создать новую задачу",
    description="Создаёт новую задачу для текущего аутентифицированного пользователя. Требуется передать данные задачи в формате JSON.",
    responses={
        200: {
            "description": "Задача успешно создана",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "title": "Новая задача",
                        "description": "Описание задачи",
                        "status": "open",
                        "priority": 1,
                        "owner_id": 1,
                        "created_at": "2025-05-07T12:00:00Z"
                    }
                }
            }
        },
        401: {"description": "Пользователь не аутентифицирован"},
        422: {"description": "Некорректные входные данные"}
    }
)
async def create_task(
    task: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    db_task = Task(**task.dict(), owner_id=current_user.id)
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task

@router.put(
    "/{task_id}",
    response_model=TaskOut,
    summary="Обновить задачу",
    description="Обновляет существующую задачу по её ID. Можно обновить только те поля, которые переданы в запросе. Задача должна принадлежать текущему пользователю.",
    responses={
        200: {
            "description": "Задача успешно обновлена",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "title": "Обновлённая задача",
                        "description": "Новое описание",
                        "status": "in_progress",
                        "priority": 2,
                        "owner_id": 1,
                        "created_at": "2025-05-07T12:00:00Z"
                    }
                }
            }
        },
        401: {"description": "Пользователь не аутентифицирован"},
        404: {"description": "Задача не найдена"},
        422: {"description": "Некорректные входные данные"}
    }
)
async def update_task(
    task_id: int,
    task: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
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

@router.get(
    "",
    response_model=List[TaskOut],
    summary="Получить список задач",
    description="Возвращает список задач текущего пользователя с возможностью фильтрации по статусу, приоритету или дате создания.",
    responses={
        200: {
            "description": "Список задач успешно возвращён",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "title": "Задача 1",
                            "description": "Описание 1",
                            "status": "open",
                            "priority": 1,
                            "owner_id": 1,
                            "created_at": "2025-05-07T12:00:00Z"
                        },
                        {
                            "id": 2,
                            "title": "Задача 2",
                            "description": "Описание 2",
                            "status": "closed",
                            "priority": 2,
                            "owner_id": 1,
                            "created_at": "2025-05-07T13:00:00Z"
                        }
                    ]
                }
            }
        },
        401: {"description": "Пользователь не аутентифицирован"}
    }
)
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

@router.get(
    "/search",
    response_model=List[TaskOut],
    summary="Поиск задач",
    description="Ищет задачи текущего пользователя по ключевому слову в заголовке или описании задачи.",
    responses={
        200: {
            "description": "Результаты поиска успешно возвращены",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "title": "Задача 1",
                            "description": "Описание с ключевым словом",
                            "status": "open",
                            "priority": 1,
                            "owner_id": 1,
                            "created_at": "2025-05-07T12:00:00Z"
                        }
                    ]
                }
            }
        },
        401: {"description": "Пользователь не аутентифицирован"},
        422: {"description": "Параметр поиска отсутствует или некорректен"}
    }
)
async def search_tasks(
    q: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Task).filter(Task.owner_id == current_user.id).filter(
        (Task.title.contains(q)) | (Task.description.contains(q))
    )
    result = await db.execute(query)
    return result.scalars().all()