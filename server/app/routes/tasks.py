from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from ..db import get_session
from ..models import Task, UserProfile, Achievement, Goal
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
    # Clamp XP into difficulty range
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
    
    # Recalculate/clamp XP if difficulty or xp changed
    if "difficulty" in payload or "xp" in payload:
        task.xp = task.calculate_xp_reward()
    
    task.updated_at = datetime.utcnow()
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@router.post("/{task_id}/toggle-active")
def toggle_task_active(task_id: int, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.completed:
        raise HTTPException(status_code=400, detail="Cannot activate completed tasks")
    
    task.active = not task.active
    task.updated_at = datetime.utcnow()
    session.add(task)
    session.commit()
    session.refresh(task)
    return {"task": task, "message": f"Task {'activated' if task.active else 'deactivated'}"}


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
    
    # Use clamped task XP directly
    xp_reward = task.xp
    profile.xp += xp_reward
    
    # Update level and skill points
    new_level = profile.calculate_level()
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

    # Recalculate level again in case achievements granted XP
    profile.level = profile.calculate_level()
    
    # Update goal progress based on task completion
    goal_updates = update_goal_progress(task, session)
    
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
        "skill_bonuses": skill_bonuses,
        "goal_progress": goal_updates
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

def update_goal_progress(task: Task, session: Session) -> List[Dict]:
    """Update goal progress based on completed task"""
    goal_updates = []
    
    # Get all active goals that might be related to this task
    active_goals = session.exec(
        select(Goal).where(Goal.user_id == 1, Goal.completed == False)
    ).all()
    
    if not active_goals:
        return goal_updates
    
    # Calculate progress increase based on task properties
    base_progress_increase = 0.0
    
    # Base progress based on difficulty
    difficulty_progress = {
        "easy": 0.05,     # 5% progress
        "medium": 0.08,   # 8% progress  
        "hard": 0.12,     # 12% progress
        "expert": 0.20    # 20% progress
    }
    base_progress_increase = difficulty_progress.get(task.difficulty, 0.05)
    
    # Bonus for high goal alignment
    if hasattr(task, 'goal_alignment_score') and task.goal_alignment_score:
        alignment_bonus = task.goal_alignment_score * 0.1  # Up to 10% bonus
    else:
        alignment_bonus = task.goal_alignment * 0.1 if hasattr(task, 'goal_alignment') else 0.0
    
    total_progress_increase = base_progress_increase + alignment_bonus
    
    # Update goals based on category and content matching
    for goal in active_goals:
        progress_added = 0.0
        reason = ""
        
        # Category matching
        if task.category == goal.category:
            progress_added = total_progress_increase
            reason = f"Task category '{task.category}' matches goal"
        # Keyword matching in titles/descriptions
        elif goal.title.lower() in task.title.lower() or task.title.lower() in goal.title.lower():
            progress_added = total_progress_increase * 0.8  # 80% for keyword match
            reason = f"Task relates to goal '{goal.title}'"
        # General learning/growth tasks boost personal goals
        elif goal.category == "personal" and task.category in ["learning", "health"]:
            progress_added = total_progress_increase * 0.3  # 30% for general growth
            reason = f"General growth task supports personal development"
        
        # Apply progress update
        if progress_added > 0:
            old_progress = goal.progress
            goal.progress = min(goal.progress + progress_added, 1.0)  # Cap at 100%
            goal.updated_at = datetime.utcnow()
            
            # Mark as completed if reached 100%
            if goal.progress >= 1.0 and not goal.completed:
                goal.completed = True
                goal.completed_at = datetime.utcnow()
                reason += " - GOAL COMPLETED! 🎉"
            
            goal_updates.append({
                "goal_id": goal.id,
                "goal_title": goal.title,
                "old_progress": old_progress,
                "new_progress": goal.progress,
                "progress_added": progress_added,
                "reason": reason,
                "completed": goal.completed
            })
            
            session.add(goal)
    
    return goal_updates
