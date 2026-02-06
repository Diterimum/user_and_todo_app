from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from db import get_db
from models.orm import Todo
from models.schemas import TodoCreateIn, TodoStatusIn, TodoDeleteIn, TodoOut
from controllers.auth import get_user_by_token

router = APIRouter(tags=["todos"])


@router.get("/todos", response_model=List[TodoOut])
def list_todos(
    Authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    user_id, _ = get_user_by_token(Authorization, db)

    stmt = (
        select(Todo)
        .where(Todo.user_id == user_id)
        .order_by(desc(Todo.created_at))
    )
    todos = db.execute(stmt).scalars().all()
    return [{"task": t.task, "status": t.status, "created_at": t.created_at} for t in todos]


@router.get("/todos/not-completed", response_model=List[TodoOut])
def list_not_completed(
    Authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    user_id, _ = get_user_by_token(Authorization, db)

    stmt = (
        select(Todo)
        .where(Todo.user_id == user_id, Todo.status == False)
        .order_by(desc(Todo.created_at))
    )
    todos = db.execute(stmt).scalars().all()
    return [{"task": t.task, "status": t.status, "created_at": t.created_at} for t in todos]


@router.post("/todos", response_model=TodoOut, status_code=201)
def add_todo(
    payload: TodoCreateIn,
    Authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    user_id, _ = get_user_by_token(Authorization, db)

    stmt = select(Todo).where(Todo.user_id == user_id, Todo.task == payload.task)
    exists = db.execute(stmt).scalars().first()
    if exists:
        raise HTTPException(status_code=400, detail="Task with same text already exists")

    t = Todo(user_id=user_id, task=payload.task)
    db.add(t)
    db.commit()
    db.refresh(t)

    return {"task": t.task, "status": t.status, "created_at": t.created_at}


@router.patch("/todos/status", response_model=TodoOut)
def set_status(
    payload: TodoStatusIn,
    Authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    user_id, _ = get_user_by_token(Authorization, db)

    stmt = select(Todo).where(Todo.user_id == user_id, Todo.task == payload.task)
    t = db.execute(stmt).scalars().first()
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")

    t.status = payload.status
    db.commit()
    db.refresh(t)

    return {"task": t.task, "status": t.status, "created_at": t.created_at}


@router.delete("/todos")
def delete_todo(
    payload: TodoDeleteIn,
    Authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    user_id, _ = get_user_by_token(Authorization, db)

    stmt = select(Todo).where(Todo.user_id == user_id, Todo.task == payload.task)
    t = db.execute(stmt).scalars().first()
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(t)
    db.commit()
    return {"ok": True}