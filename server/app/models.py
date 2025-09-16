from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime


class UserProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=1, primary_key=True)
    name: str = "Player"
    xp: int = 0
    skill_points: int = 0
    goals: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    frequency: str = Field(description="daily|weekly|monthly")
    xp: int = 10
    completed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
