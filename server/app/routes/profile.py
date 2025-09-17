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
    
    # Safe fields that can be updated
    updatable_fields = {
        'name', 'goals', 'preferred_difficulty', 'focus_areas',
        'strength', 'endurance', 'agility', 'focus', 'memory', 
        'problem_solving', 'communication', 'leadership', 'empathy'
    }
    
    for key, value in payload.items():
        if key in updatable_fields and hasattr(profile, key):
            setattr(profile, key, value)
    
    profile.updated_at = datetime.utcnow()
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile
