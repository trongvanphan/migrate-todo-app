from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Task
from app.schemas import TaskCreate, TaskOut, TaskUpdate
from app.security import CurrentUser

router = APIRouter(prefix="/tasks", tags=["tasks"])

Filter = Literal["all", "active", "completed"]


def _owned_task(db: Session, task_id: int, owner_id: int) -> Task:
    task = db.get(Task, task_id)
    if task is None or task.owner_id != owner_id:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("", response_model=list[TaskOut])
def list_tasks(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    filter: Filter = Query("all"),
) -> list[Task]:
    stmt = select(Task).where(Task.owner_id == current_user.id).order_by(Task.created_at.desc())
    if filter == "active":
        stmt = stmt.where(Task.completed.is_(False))
    elif filter == "completed":
        stmt = stmt.where(Task.completed.is_(True))
    return list(db.scalars(stmt).all())


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Task:
    task = Task(owner_id=current_user.id, title=payload.title, completed=False)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Task:
    task = _owned_task(db, task_id, current_user.id)
    if payload.title is not None:
        task.title = payload.title
    if payload.completed is not None:
        task.completed = payload.completed
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_task(
    task_id: int,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    task = _owned_task(db, task_id, current_user.id)
    db.delete(task)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
