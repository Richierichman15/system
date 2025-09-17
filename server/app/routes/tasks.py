from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from ..db import get_session
from ..models import Task, UserProfile, Achievement
from sqlmodel import Session
from datetime import datetime, timedelta
import json


router = APIRouter()


@router.get("/", response_model=List[Task])
def list_tasks(
    session: Session = Depends(get_session),
    category: str = None,
    completed: bool = None
):
    query = select(Task).order_by(Task.created_at.desc())
    
    if category:
        query = query.where(Task.category == category)
    if completed is not None:
        query = query.where(Task.completed == completed)
    
    return session.exec(query).all()


@router.post("/", response_model=Task)
def create_task(task: Task, session: Session = Depends(get_session)):
    task.id = None
    # Calculate XP based on difficulty
    task.xp = task.calculate_xp_reward()
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@router.patch("/{task_id}", response_model=Task)
def update_task(task_id: int, payload: dict, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    for key, value in payload.items():
        if hasattr(task, key) and key != "id":
            setattr(task, key, value)
    
    # Recalculate XP if difficulty changed
    if "difficulty" in payload:
        task.xp = task.calculate_xp_reward()
    
    task.updated_at = datetime.utcnow()
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@router.delete("/{task_id}")
def delete_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    session.delete(task)
    session.commit()
    return {"message": "Task deleted successfully"}


@router.post("/{task_id}/complete")
def complete_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.completed:
        return {"task": task, "level_up": False, "achievements": []}

    # Get profile
    profile = session.get(UserProfile, 1)
    if not profile:
        profile = UserProfile(id=1)
        session.add(profile)
        session.flush()

    # Store old level for level-up detection  
    old_level = profile.level
    old_xp = profile.xp
    
    # Complete task
    task.completed = True
    task.completed_at = datetime.utcnow()
    task.updated_at = datetime.utcnow()
    
    # Calculate XP reward based on difficulty
    xp_reward = task.calculate_xp_reward()
    profile.xp += xp_reward
    
    # Update level and skill points
    new_level = profile.calculate_level()
    old_level = profile.level
    profile.level = new_level
    
    # Award skill points based on level, not raw XP
    # 1 skill point per level + bonus skill points for higher levels
    base_skill_points = profile.level - 1  # 1 skill point per level beyond 1
    bonus_skill_points = max(0, (profile.level - 10) * 2) if profile.level > 10 else 0  # 2 extra per level after 10
    profile.skill_points = base_skill_points + bonus_skill_points
    
    # Apply skill bonuses if any
    skill_bonuses = {}
    if task.skill_bonuses:
        try:
            skill_bonuses = json.loads(task.skill_bonuses)
            for skill, bonus in skill_bonuses.items():
                if hasattr(profile, skill):
                    current_value = getattr(profile, skill)
                    setattr(profile, skill, current_value + bonus)
        except (json.JSONDecodeError, TypeError):
            pass
    
    # Create recurring task if needed
    if task.is_recurring and task.recurring_interval:
        new_task = Task(
            title=task.title,
            description=task.description,
            frequency=task.frequency,
            difficulty=task.difficulty,
            category=task.category,
            xp=task.xp,
            skill_bonuses=task.skill_bonuses,
            is_recurring=True,
            recurring_interval=task.recurring_interval,
            created_at=datetime.utcnow() + timedelta(days=task.recurring_interval)
        )
        session.add(new_task)
    
    profile.updated_at = datetime.utcnow()
    
    # Check for achievements
    new_achievements = check_achievements(profile, session)
    
    session.add(task)
    session.add(profile)
    session.commit()
    session.refresh(task)
    session.refresh(profile)
    
    return {
        "task": task,
        "profile": profile,
        "xp_gained": xp_reward,
        "level_up": new_level > old_level,
        "old_level": old_level,
        "new_level": new_level,
        "achievements": new_achievements,
        "skill_bonuses": skill_bonuses
    }


@router.get("/categories")
def get_task_categories():
    return {
        "categories": [
            {"id": "career", "name": "Career & Work", "icon": "fa-briefcase", "color": "#3B82F6"},
            {"id": "health", "name": "Health & Fitness", "icon": "fa-heart", "color": "#10B981"},
            {"id": "personal", "name": "Personal Development", "icon": "fa-user-plus", "color": "#8B5CF6"},
            {"id": "financial", "name": "Financial", "icon": "fa-dollar-sign", "color": "#F59E0B"},
            {"id": "learning", "name": "Learning & Education", "icon": "fa-graduation-cap", "color": "#EF4444"},
            {"id": "relationships", "name": "Relationships & Social", "icon": "fa-users", "color": "#EC4899"},
            {"id": "general", "name": "General", "icon": "fa-star", "color": "#6B7280"}
        ]
    }


def check_achievements(profile: UserProfile, session: Session) -> List[Achievement]:
    """Check and unlock new achievements for the user"""
    new_achievements = []
    
    # Get all locked achievements
    achievements = session.exec(
        select(Achievement).where(Achievement.unlocked == False)
    ).all()
    
    for achievement in achievements:
        should_unlock = False
        
        if achievement.condition_type == "level_reached":
            should_unlock = profile.level >= achievement.condition_value
        elif achievement.condition_type == "xp_earned":
            should_unlock = profile.xp >= achievement.condition_value
        elif achievement.condition_type == "tasks_completed":
            completed_tasks = session.exec(
                select(Task).where(Task.completed == True)
            ).all()
            should_unlock = len(completed_tasks) >= achievement.condition_value
        
        if should_unlock:
            achievement.unlocked = True
            achievement.unlocked_at = datetime.utcnow()
            profile.xp += achievement.xp_reward
            session.add(achievement)
            new_achievements.append(achievement)
    
    return new_achievements