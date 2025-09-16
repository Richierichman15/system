from typing import List
from fastapi import APIRouter, Depends
from sqlmodel import select, Session
from ..db import get_session
from ..models import Achievement, UserProfile
from datetime import datetime


router = APIRouter()


@router.get("/", response_model=List[Achievement])
def list_achievements(session: Session = Depends(get_session)):
    """Get all achievements"""
    return session.exec(select(Achievement).order_by(Achievement.created_at)).all()


@router.get("/unlocked", response_model=List[Achievement])
def get_unlocked_achievements(session: Session = Depends(get_session)):
    """Get all unlocked achievements"""
    return session.exec(
        select(Achievement).where(Achievement.unlocked == True)
        .order_by(Achievement.unlocked_at.desc())
    ).all()


@router.post("/initialize")
def initialize_achievements(session: Session = Depends(get_session)):
    """Initialize default achievements"""
    # Check if achievements already exist
    existing = session.exec(select(Achievement)).first()
    if existing:
        return {"message": "Achievements already initialized"}
    
    default_achievements = [
        # Level-based achievements
        Achievement(
            name="First Steps",
            description="Reach Level 2",
            icon="fa-baby",
            xp_reward=50,
            category="progression",
            condition_type="level_reached",
            condition_value=2
        ),
        Achievement(
            name="Getting Serious",
            description="Reach Level 5",
            icon="fa-rocket",
            xp_reward=100,
            category="progression",
            condition_type="level_reached",
            condition_value=5
        ),
        Achievement(
            name="Veteran",
            description="Reach Level 10",
            icon="fa-medal",
            xp_reward=200,
            category="progression",
            condition_type="level_reached",
            condition_value=10
        ),
        Achievement(
            name="Master",
            description="Reach Level 20",
            icon="fa-crown",
            xp_reward=500,
            category="progression",
            condition_type="level_reached",
            condition_value=20
        ),
        
        # Task completion achievements
        Achievement(
            name="Getting Started",
            description="Complete your first task",
            icon="fa-check",
            xp_reward=25,
            category="tasks",
            condition_type="tasks_completed",
            condition_value=1
        ),
        Achievement(
            name="Task Warrior",
            description="Complete 10 tasks",
            icon="fa-sword",
            xp_reward=75,
            category="tasks",
            condition_type="tasks_completed",
            condition_value=10
        ),
        Achievement(
            name="Quest Master",
            description="Complete 25 tasks",
            icon="fa-trophy",
            xp_reward=150,
            category="tasks",
            condition_type="tasks_completed",
            condition_value=25
        ),
        Achievement(
            name="Completionist",
            description="Complete 100 tasks",
            icon="fa-star",
            xp_reward=500,
            category="tasks",
            condition_type="tasks_completed",
            condition_value=100
        ),
        
        # XP-based achievements
        Achievement(
            name="Experience Seeker",
            description="Earn 500 XP",
            icon="fa-gem",
            xp_reward=50,
            category="progression",
            condition_type="xp_earned",
            condition_value=500
        ),
        Achievement(
            name="Knowledge Hunter",
            description="Earn 1000 XP",
            icon="fa-brain",
            xp_reward=100,
            category="progression",
            condition_type="xp_earned",
            condition_value=1000
        ),
        Achievement(
            name="Wisdom Collector",
            description="Earn 5000 XP",
            icon="fa-scroll",
            xp_reward=300,
            category="progression",
            condition_type="xp_earned",
            condition_value=5000
        )
    ]
    
    for achievement in default_achievements:
        session.add(achievement)
    
    session.commit()
    return {"message": f"Initialized {len(default_achievements)} achievements"}


@router.get("/stats")
def get_achievement_stats(session: Session = Depends(get_session)):
    """Get achievement statistics"""
    total_achievements = session.exec(select(Achievement)).all()
    unlocked_achievements = session.exec(
        select(Achievement).where(Achievement.unlocked == True)
    ).all()
    
    return {
        "total": len(total_achievements),
        "unlocked": len(unlocked_achievements),
        "progress": len(unlocked_achievements) / len(total_achievements) if total_achievements else 0,
        "categories": {}
    }