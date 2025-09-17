from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime, date
import math
import json


class Goal(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    category: str = Field(default="personal", description="career|health|personal|financial|learning|relationships")
    priority: str = Field(default="medium", description="low|medium|high|critical")
    target_date: Optional[date] = None
    progress: float = Field(default=0.0, description="0.0 to 1.0")
    completed: bool = Field(default=False)
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    user_id: Optional[int] = Field(default=1, foreign_key="userprofile.id")
    user: Optional["UserProfile"] = Relationship(back_populates="user_goals")


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
    
    # Goal preferences
    goals: Optional[str] = None  # Legacy field for backward compatibility
    preferred_difficulty: str = Field(default="medium", description="easy|medium|hard|expert")
    focus_areas: Optional[str] = Field(default=None, description="JSON array of focus categories")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def calculate_level(self) -> int:
        """Calculate level based on XP using challenging exponential scaling"""
        if self.xp <= 0:
            return 1
        
        # More challenging progression - each level requires significantly more XP
        # Level 2 = 100 XP, Level 3 = 300 XP, Level 4 = 600 XP, Level 5 = 1000 XP, etc.
        # Formula: level = floor(sqrt(xp/25)) * 0.5 + 1, but with discrete level thresholds
        
        level_thresholds = [
            0,      # Level 1
            100,    # Level 2 
            300,    # Level 3
            600,    # Level 4
            1000,   # Level 5
            1500,   # Level 6
            2100,   # Level 7
            2800,   # Level 8
            3600,   # Level 9
            4500,   # Level 10
            5500,   # Level 11
            6600,   # Level 12
            7800,   # Level 13
            9100,   # Level 14
            10500,  # Level 15
            12000,  # Level 16
            13600,  # Level 17
            15300,  # Level 18
            17100,  # Level 19
            19000,  # Level 20
        ]
        
        for level, threshold in enumerate(level_thresholds):
            if self.xp < threshold:
                return max(1, level)
        
        # For levels beyond 20, use exponential formula
        # Each level past 20 requires 2000 more XP than the previous gap
        if self.xp >= 19000:
            excess_xp = self.xp - 19000
            additional_levels = int(excess_xp // 2500)  # 2500 XP per level beyond 20
            return min(20 + additional_levels, 50)  # Cap at level 50
        
        return 20
    
    def xp_for_next_level(self) -> int:
        """Calculate XP needed for next level"""
        current_level = self.calculate_level()
        
        level_thresholds = [
            0, 100, 300, 600, 1000, 1500, 2100, 2800, 3600, 4500, 5500,
            6600, 7800, 9100, 10500, 12000, 13600, 15300, 17100, 19000
        ]
        
        if current_level < len(level_thresholds):
            return level_thresholds[current_level]
        else:
            # For levels beyond 20
            return 19000 + ((current_level - 19) * 2500)
    
    def xp_for_current_level(self) -> int:
        """Calculate XP needed for current level"""
        current_level = self.calculate_level()
        if current_level <= 1:
            return 0
            
        level_thresholds = [
            0, 100, 300, 600, 1000, 1500, 2100, 2800, 3600, 4500, 5500,
            6600, 7800, 9100, 10500, 12000, 13600, 15300, 17100, 19000
        ]
        
        if current_level <= len(level_thresholds):
            return level_thresholds[current_level - 1]
        else:
            # For levels beyond 20
            return 19000 + ((current_level - 20) * 2500)
    
    def progress_to_next_level(self) -> float:
        """Calculate progress percentage to next level (0.0 to 1.0)"""
        current_level_xp = self.xp_for_current_level()
        next_level_xp = self.xp_for_next_level()
        progress_xp = self.xp - current_level_xp
        needed_xp = next_level_xp - current_level_xp
        return min(progress_xp / needed_xp if needed_xp > 0 else 0.0, 1.0)
    
    def get_focus_areas(self) -> List[str]:
        """Get list of focus areas"""
        if not self.focus_areas:
            return []
        try:
            return json.loads(self.focus_areas)
        except:
            return []
    
    def set_focus_areas(self, areas: List[str]):
        """Set focus areas as JSON"""
        self.focus_areas = json.dumps(areas)
    
    # Relationships
    tasks: List["Task"] = Relationship(back_populates="user")
    user_goals: List["Goal"] = Relationship(back_populates="user")
    achievements: List["Achievement"] = Relationship(back_populates="user")


class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    frequency: str = Field(description="daily|weekly|monthly")
    difficulty: str = Field(default="medium", description="easy|medium|hard|expert")
    category: str = Field(default="general", description="career|health|personal|financial|learning|relationships|general")
    xp: int = 10
    skill_bonuses: Optional[str] = Field(default=None, description="JSON string of skill bonuses")
    goal_alignment: float = Field(default=0.5, description="How well this task aligns with user goals (0.0 to 1.0)")
    is_recurring: bool = Field(default=False)
    recurring_interval: Optional[int] = Field(default=None, description="Days between recurrence")
    active: bool = Field(default=False, description="Whether the task is actively being pursued")
    completed: bool = False
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    user_id: Optional[int] = Field(default=1, foreign_key="userprofile.id")
    user: Optional["UserProfile"] = Relationship(back_populates="tasks")
    
    def calculate_xp_reward(self, base_xp: int = None) -> int:
        """Calculate XP reward based on difficulty and goal alignment"""
        if base_xp is None:
            base_xp = self.xp
            
        difficulty_multipliers = {
            "easy": 0.7,
            "medium": 1.0,
            "hard": 1.5,
            "expert": 2.0
        }
        
        # Bonus XP for well-aligned tasks
        alignment_bonus = 1.0 + (self.goal_alignment * 0.5)  # Up to 50% bonus
        
        return int(base_xp * difficulty_multipliers.get(self.difficulty, 1.0) * alignment_bonus)


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
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    user_id: Optional[int] = Field(default=1, foreign_key="userprofile.id")
    user: Optional["UserProfile"] = Relationship(back_populates="achievements")