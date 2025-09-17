from fastapi import APIRouter, Depends
from sqlmodel import Session
from ..db import get_session
from ..models import UserProfile
from datetime import datetime


router = APIRouter()


@router.get("/")
def get_profile(session: Session = Depends(get_session)):
    profile = session.get(UserProfile, 1)
    if not profile:
        profile = UserProfile(id=1)
        session.add(profile)
        session.commit()
        session.refresh(profile)
    return profile


@router.patch("/")
def update_profile(payload: dict, session: Session = Depends(get_session)):
    profile = session.get(UserProfile, 1)
    if not profile:
        profile = UserProfile(id=1)
        session.add(profile)
        session.flush()
    
    # Store original skill values to calculate spent points
    skill_fields = {
        'strength', 'endurance', 'agility', 'focus', 'memory', 
        'problem_solving', 'communication', 'leadership', 'empathy'
    }
    
    original_skills = {}
    for skill in skill_fields:
        original_skills[skill] = getattr(profile, skill, 1)
    
    # Safe fields that can be updated
    updatable_fields = {
        'name', 'goals', 'preferred_difficulty', 'focus_areas', 'skill_points',
        'strength', 'endurance', 'agility', 'focus', 'memory', 
        'problem_solving', 'communication', 'leadership', 'empathy'
    }
    
    # Calculate skill points that would be spent
    skill_points_to_spend = 0
    for key, new_value in payload.items():
        if key in skill_fields and key in payload:
            old_value = original_skills[key]
            if new_value > old_value:
                skill_points_to_spend += (new_value - old_value)
    
    # Validate skill point spending
    if skill_points_to_spend > profile.skill_points:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400, 
            detail=f"Not enough skill points. Need {skill_points_to_spend}, have {profile.skill_points}"
        )
    
    # Apply updates
    for key, value in payload.items():
        if key in updatable_fields and hasattr(profile, key):
            setattr(profile, key, value)
    
    # Deduct spent skill points
    if skill_points_to_spend > 0:
        profile.skill_points -= skill_points_to_spend
    
    profile.updated_at = datetime.utcnow()
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile
