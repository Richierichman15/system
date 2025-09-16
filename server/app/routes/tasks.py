from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from ..db import get_session
from ..models import Task, UserProfile
from sqlmodel import Session
from datetime import datetime


router = APIRouter()


@router.get("/", response_model=List[Task])
def list_tasks(session: Session = Depends(get_session)):
    return session.exec(select(Task).order_by(Task.created_at.desc())).all()


@router.post("/", response_model=Task)
def create_task(task: Task, session: Session = Depends(get_session)):
    task.id = None
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@router.patch("/{task_id}/complete", response_model=Task)
def complete_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.completed:
        return task

    task.completed = True
    task.updated_at = datetime.utcnow()

    profile = session.get(UserProfile, 1)
    if not profile:
        profile = UserProfile(id=1)
        session.add(profile)
        session.flush()

    profile.xp += task.xp
    # Grant 1 skill point per 100 xp earned in total
    profile.skill_points = profile.xp // 100
    profile.updated_at = datetime.utcnow()

    session.add(task)
    session.add(profile)
    session.commit()
    session.refresh(task)
    return task
