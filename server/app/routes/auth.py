from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session
from ..db import get_session
from ..models import UserProfile


router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(payload: LoginRequest, session: Session = Depends(get_session)):
    if not (payload.username == "buck" and payload.password == "nasty"):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    profile = session.get(UserProfile, 1)
    if not profile:
        profile = UserProfile(id=1)
        session.add(profile)
        session.commit()
        session.refresh(profile)

    is_new_user = not bool(profile.goals)
    token = "buck-token"

    return {
        "token": token,
        "is_new_user": is_new_user,
        "profile": profile.model_dump() if hasattr(profile, "model_dump") else profile.dict(),
    }


