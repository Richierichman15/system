from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime
import math


class UserProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=1, primary_key=True)
    name: str = "Player"
    xp: int = 0
    skill_points: int = 0
    level: int = Field(default=1)
    
    # Individual stats
    strength: int = Field(default=1)
    endurance: int = Field(default=1)
    agility: int = Field(default=1)
    focus: int = Field(default=1)
    memory: int = Field(default=1)
    problem_solving: int = Field(default=1)
    communication: int = Field(default=1)
    leadership: int = Field(default=1)
    empathy: int = Field(default=1)
    
    goals: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def calculate_level(self) -> int:
        """Calculate level based on XP using exponential scaling"""
        if self.xp <= 0:
            return 1
        # Level formula: level = floor(sqrt(xp/50)) + 1
        # This means: Level 2 = 50 XP, Level 3 = 200 XP, Level 4 = 450 XP, etc.
        return int(math.sqrt(self.xp / 50)) + 1
    
    def xp_for_next_level(self) -> int:
        """Calculate XP needed for next level"""
        next_level = self.level + 1
        return ((next_level - 1) ** 2) * 50
    
    def xp_for_current_level(self) -> int:
        """Calculate XP needed for current level"""
        if self.level <= 1:
            return 0
        return ((self.level - 1) ** 2) * 50
    
    def progress_to_next_level(self) -> float:
        """Calculate progress percentage to next level (0.0 to 1.0)"""
        current_level_xp = self.xp_for_current_level()
        next_level_xp = self.xp_for_next_level()
        progress_xp = self.xp - current_level_xp
        needed_xp = next_level_xp - current_level_xp
        return min(progress_xp / needed_xp if needed_xp > 0 else 0.0, 1.0)


class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    frequency: str = Field(description="daily|weekly|monthly")
    difficulty: str = Field(default="medium", description="easy|medium|hard|expert")
    category: str = Field(default="general", description="work|fitness|learning|social|personal|general")
    xp: int = 10
    skill_bonuses: Optional[str] = Field(default=None, description="JSON string of skill bonuses")
    goal_alignment: Optional[float] = Field(default=0.0, description="How well this task aligns with user goals (0.0 to 1.0)")
    is_recurring: bool = Field(default=False)
    recurring_interval: Optional[int] = Field(default=None, description="Days between recurrence")
    active: bool = Field(default=True, description="Whether the task is currently active")
    completed: bool = False
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def calculate_xp_reward(self, base_xp: int = None) -> int:
        """Calculate XP reward based on difficulty"""
        if base_xp is None:
            base_xp = self.xp
            
        multipliers = {
            "easy": 0.7,
            "medium": 1.0,
            "hard": 1.5,
            "expert": 2.0
        }
        return int(base_xp * multipliers.get(self.difficulty, 1.0))


class Goal(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(default=1)
    title: str
    description: Optional[str] = None
    category: str = Field(default="personal")
    priority: str = Field(default="medium", description="critical|high|medium|low")
    target_date: Optional[str] = None
    progress: float = Field(default=0.0, description="Progress from 0.0 to 1.0")
    completed: bool = Field(default=False)
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Achievement(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: str
    icon: str
    xp_reward: int = 0
    category: str
    condition_type: str = Field(description="tasks_completed|xp_earned|level_reached|streak|skill_level")
    condition_value: int
    unlocked: bool = Field(default=False)
    unlocked_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
