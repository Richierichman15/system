from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select, Session
from ..db import get_session
from ..models import Goal, UserProfile
from datetime import datetime


router = APIRouter()


@router.get("/", response_model=List[Goal])
def list_goals(session: Session = Depends(get_session)):
    """Get all active goals"""
    return session.exec(select(Goal).where(Goal.is_active == True).order_by(Goal.priority.desc(), Goal.created_at.desc())).all()


@router.post("/", response_model=Goal)
def create_goal(goal_data: dict, session: Session = Depends(get_session)):
    """Create a new goal"""
    goal = Goal(**goal_data)
    goal.created_at = datetime.utcnow()
    goal.updated_at = datetime.utcnow()
    session.add(goal)
    session.commit()
    session.refresh(goal)
    return goal


@router.patch("/{goal_id}", response_model=Goal)
def update_goal(goal_id: int, goal_data: dict, session: Session = Depends(get_session)):
    """Update an existing goal"""
    goal = session.get(Goal, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    for key, value in goal_data.items():
        if hasattr(goal, key):
            setattr(goal, key, value)
    
    goal.updated_at = datetime.utcnow()
    session.add(goal)
    session.commit()
    session.refresh(goal)
    return goal


@router.delete("/{goal_id}")
def delete_goal(goal_id: int, session: Session = Depends(get_session)):
    """Delete (deactivate) a goal"""
    goal = session.get(Goal, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    goal.is_active = False
    goal.updated_at = datetime.utcnow()
    session.add(goal)
    session.commit()
    return {"message": "Goal deactivated successfully"}


@router.post("/{goal_id}/progress")
def update_goal_progress(goal_id: int, progress_data: dict, session: Session = Depends(get_session)):
    """Update goal progress"""
    goal = session.get(Goal, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    progress = progress_data.get("progress", 0.0)
    progress = max(0.0, min(1.0, progress))  # Clamp between 0 and 1
    
    goal.progress = progress
    goal.updated_at = datetime.utcnow()
    session.add(goal)
    session.commit()
    session.refresh(goal)
    return goal


@router.get("/categories")
def get_goal_categories():
    """Get available goal categories"""
    return {
        "categories": [
            {"id": "career", "name": "Career & Work", "icon": "fas fa-briefcase"},
            {"id": "health", "name": "Health & Fitness", "icon": "fas fa-heart"},
            {"id": "personal", "name": "Personal Development", "icon": "fas fa-user-plus"},
            {"id": "financial", "name": "Financial", "icon": "fas fa-dollar-sign"},
            {"id": "learning", "name": "Learning & Education", "icon": "fas fa-graduation-cap"},
            {"id": "relationships", "name": "Relationships & Social", "icon": "fas fa-users"}
        ]
    }
