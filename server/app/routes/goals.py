from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select, Session
from ..db import get_session
from ..models import Goal, UserProfile
from datetime import datetime, date


router = APIRouter()


@router.get("/", response_model=List[Goal])
def list_goals(session: Session = Depends(get_session)):
    """Get all goals for user 1 (completed and active)"""
    return session.exec(select(Goal).where(Goal.user_id == 1).order_by(Goal.completed.asc(), Goal.priority.desc(), Goal.created_at.desc())).all()


@router.post("/", response_model=Goal)
def create_goal(goal_data: dict, session: Session = Depends(get_session)):
    """Create a new goal"""
    # Ensure user exists
    user = session.get(UserProfile, 1)
    if not user:
        user = UserProfile(id=1)
        session.add(user)
        session.flush()
    
    # Parse target_date if it's a string
    if "target_date" in goal_data and goal_data["target_date"]:
        try:
            if isinstance(goal_data["target_date"], str):
                goal_data["target_date"] = date.fromisoformat(goal_data["target_date"])
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    goal = Goal(**goal_data)
    goal.user_id = 1
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
    """Delete a goal"""
    goal = session.get(Goal, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    session.delete(goal)
    session.commit()
    return {"message": "Goal deleted successfully"}


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


@router.post("/{goal_id}/complete")
def complete_goal(goal_id: int, session: Session = Depends(get_session)):
    """Complete a goal and reward XP"""
    goal = session.get(Goal, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    if goal.completed:
        return {"goal": goal, "xp_gained": 0, "message": "Goal already completed"}
    
    # Get or create user profile
    profile = session.get(UserProfile, 1)
    if not profile:
        profile = UserProfile(id=1)
        session.add(profile)
        session.flush()
    
    # Calculate XP reward based on goal priority and category
    xp_rewards = {
        "critical": 50,  # Highest priority gets max XP
        "high": 40,
        "medium": 30,
        "low": 20      # Lowest priority gets min XP
    }
    
    base_xp = xp_rewards.get(goal.priority, 30)
    
    # Bonus XP for certain categories
    category_bonuses = {
        "career": 10,     # Career goals are important
        "learning": 5,    # Learning gets a bonus
        "health": 5,      # Health goals are valuable
        "financial": 10,  # Financial goals get higher reward
    }
    
    bonus_xp = category_bonuses.get(goal.category, 0)
    total_xp = base_xp + bonus_xp
    
    # Store old values for response
    old_level = profile.level
    old_xp = profile.xp
    
    # Award XP and update profile
    profile.xp += total_xp
    new_level = profile.calculate_level()
    profile.level = new_level
    
    # Award skill points based on level
    base_skill_points = profile.level - 1
    bonus_skill_points = max(0, (profile.level - 10) * 2) if profile.level > 10 else 0
    profile.skill_points = base_skill_points + bonus_skill_points
    
    # Complete the goal
    goal.completed = True
    goal.completed_at = datetime.utcnow()
    goal.progress = 1.0
    goal.updated_at = datetime.utcnow()
    
    # Save changes
    session.add(goal)
    session.add(profile)
    session.commit()
    session.refresh(goal)
    session.refresh(profile)
    
    return {
        "goal": goal,
        "profile": profile,
        "xp_gained": total_xp,
        "level_up": new_level > old_level,
        "old_level": old_level,
        "new_level": new_level,
        "message": f"Goal completed! Earned {total_xp} XP! 🎉"
    }


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
