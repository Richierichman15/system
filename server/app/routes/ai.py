from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select
from ..db import get_session
from ..models import Task, UserProfile, Goal
from typing import List, Dict, Any
import os
import json
from datetime import datetime, timedelta
import httpx
import time

try:
    import ollama
except Exception:  # pragma: no cover
    ollama = None


router = APIRouter()

# Cache for generated tasks
task_cache: Dict[str, Dict[str, Any]] = {}


def get_cached_tasks(cache_key: str):
    """Get tasks from cache if they exist and are not expired"""
    if cache_key in task_cache:
        cache_entry = task_cache[cache_key]
        # Check if cache is still valid (10 minutes)
        if datetime.utcnow() - cache_entry["timestamp"] < timedelta(minutes=10):
            return cache_entry["tasks"]
    return None


def store_in_cache(cache_key: str, tasks: List[Dict]):
    """Store tasks in cache"""
    task_cache[cache_key] = {
        "timestamp": datetime.utcnow(),
        "tasks": tasks
    }


def get_user_context(session: Session) -> Dict[str, Any]:
    """Get user profile and goals for better AI context"""
    profile = session.get(UserProfile, 1)
    if not profile:
        profile = UserProfile(id=1)
        session.add(profile)
        session.commit()
        session.refresh(profile)
    
    # Get active goals
    goals = session.exec(select(Goal).where(Goal.is_active == True)).all()
    
    context = {
        "profile": {
            "level": profile.level,
            "preferred_difficulty": profile.preferred_difficulty,
            "focus_areas": profile.get_focus_areas(),
            "legacy_goals": profile.goals or ""
        },
        "goals": [
            {
                "title": goal.title,
                "category": goal.category,
                "priority": goal.priority,
                "progress": goal.progress
            }
            for goal in goals
        ]
    }
    
    return context


def calculate_goal_alignment(task_category: str, user_goals: List[Dict]) -> float:
    """Calculate how well a task aligns with user goals"""
    if not user_goals:
        return 0.5  # Default alignment
    
    # Check for direct category matches
    for goal in user_goals:
        if goal["category"] == task_category:
            # Higher priority goals get higher alignment scores
            priority_multiplier = {
                "critical": 1.0,
                "high": 0.8,
                "medium": 0.6,
                "low": 0.4
            }.get(goal["priority"], 0.5)
            
            # Incomplete goals get higher alignment
            progress_factor = 1.0 - goal["progress"]
            
            return min(0.9, priority_multiplier * progress_factor + 0.1)
    
    return 0.3  # Low alignment if no category match


def background_ollama_request(prompt: str):
    """Make Ollama request in background to warm up the model"""
    try:
        ollama_url = "http://localhost:11434/api/generate"
        httpx.post(
            ollama_url,
            json={
                "model": "tinyllama:latest",
                "prompt": prompt,
                "options": {
                    "temperature": 0.5,
                    "top_k": 10,
                    "top_p": 0.7,
                    "num_predict": 5
                }
            },
            timeout=5.0
        )
    except Exception as e:
        print(f"Background Ollama request error: {e}")


@router.post("/generate", response_model=List[Task])
def generate_tasks(
    payload: dict, 
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    """
    Generate tasks based on user's goals and preferences using AI.
    """
    # Add rate limiting - check if tasks were generated recently
    one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
    recent_tasks = session.exec(
        select(Task).where(Task.created_at > one_minute_ago)
    ).all()
    
    if len(recent_tasks) > 0:
        raise HTTPException(
            status_code=429,
            detail="Please wait a moment before generating more tasks"
        )

    # Get user context for better AI generation
    user_context = get_user_context(session)
    frequency: str = payload.get("frequency", "daily")
    
    # Build comprehensive context for AI
    goals_text = user_context["profile"]["legacy_goals"]
    active_goals = user_context["goals"]
    focus_areas = user_context["profile"]["focus_areas"]
    difficulty = user_context["profile"]["preferred_difficulty"]
    
    # Create a rich context string
    context_parts = []
    if goals_text:
        context_parts.append(f"General goals: {goals_text}")
    
    if active_goals:
        goal_descriptions = []
        for goal in active_goals:
            progress_pct = int(goal["progress"] * 100)
            goal_descriptions.append(f"{goal['title']} ({goal['category']}, {goal['priority']} priority, {progress_pct}% complete)")
        context_parts.append(f"Specific goals: {'; '.join(goal_descriptions)}")
    
    if focus_areas:
        context_parts.append(f"Focus areas: {', '.join(focus_areas)}")
    
    full_context = "; ".join(context_parts) if context_parts else "General productivity and self-improvement"
    
    # Check cache first
    cache_key = f"{full_context[:100]}:{frequency}:{difficulty}"
    cached_items = get_cached_tasks(cache_key)
    if cached_items:
        print("Using cached tasks")
        items = cached_items
    else:
        # Generate tasks using AI
        if ollama is None:
            print("Ollama not available, using enhanced fallback tasks")
            # Enhanced fallback tasks based on user context
            categories = ["career", "health", "learning"] if not focus_areas else focus_areas[:3]
            items = []
            
            for i, category in enumerate(categories):
                base_xp = {"easy": 10, "medium": 15, "hard": 25, "expert": 40}.get(difficulty, 15)
                alignment = calculate_goal_alignment(category, active_goals)
                
                items.append({
                    "title": f"{category.title()} Focus Session",
                    "description": f"Work on {category}-related tasks for 25 minutes",
                    "frequency": frequency,
                    "category": category,
                    "difficulty": difficulty,
                    "goal_alignment": alignment,
                    "xp": base_xp
                })
                
                if len(items) >= 3:
                    break
        else:
            try:
                print("Sending request to Ollama...")
                ollama_url = "http://localhost:11434/api/generate"
                
                # Enhanced prompt with user context
                prompt = f"""Create 3 personalized tasks as JSON array:
Context: {full_context}
Frequency: {frequency}
Difficulty: {difficulty}
User Level: {user_context['profile']['level']}

Format: [{{"title":"Task Name","description":"Specific action","category":"career|health|personal|financial|learning|relationships","difficulty":"{difficulty}","xp":20}}]

Make tasks specific, actionable, and aligned with the user's goals. Categories should match their focus areas. XP should reflect difficulty: easy(10-15), medium(15-25), hard(25-40), expert(40-60)."""

                response = httpx.post(
                    ollama_url,
                    json={
                        "model": "tinyllama:latest",
                        "prompt": prompt,
                        "options": {
                            "temperature": 0.7,  # Slightly higher for more creativity
                            "top_k": 15,
                            "top_p": 0.8,
                            "num_ctx": 512,  # Larger context for better understanding
                            "num_predict": 200,
                            "mirostat": 1,
                            "mirostat_eta": 0.1,
                            "mirostat_tau": 5.0
                        }
                    },
                    timeout=15.0
                )
                
                if not response.is_success:
                    print(f"Ollama error: {response.status_code} - {response.text}")
                    raise Exception("Ollama request failed")
                    
                # Parse streaming response
                content = ""
                for line in response.iter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        if "response" in data:
                            content += data["response"]
                    except json.JSONDecodeError:
                        continue
                        
                print(f"Ollama response: {content}")
                
                # Clean up the content
                content = content.strip()
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:].strip()
                
                try:
                    items = json.loads(content)[:3]
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    print(f"Content was: {content}")
                    # Fall back to context-aware default tasks
                    items = []
                    categories = focus_areas[:3] if focus_areas else ["personal", "health", "learning"]
                    
                    for category in categories:
                        base_xp = {"easy": 10, "medium": 15, "hard": 25, "expert": 40}.get(difficulty, 15)
                        alignment = calculate_goal_alignment(category, active_goals)
                        
                        items.append({
                            "title": f"Focus on {category.title()}",
                            "description": f"Complete a {category}-related task to advance your goals",
                            "frequency": frequency,
                            "category": category,
                            "difficulty": difficulty,
                            "goal_alignment": alignment,
                            "xp": base_xp
                        })
                
                # Enhanced validation and processing
                cleaned_items = []
                for item in items:
                    if isinstance(item, dict) and "title" in item:
                        category = item.get("category", "general")
                        alignment = calculate_goal_alignment(category, active_goals)
                        
                        cleaned_item = {
                            "title": str(item.get("title", ""))[:50],
                            "description": str(item.get("description", ""))[:150],
                            "frequency": frequency,
                            "category": category,
                            "difficulty": item.get("difficulty", difficulty),
                            "goal_alignment": alignment,
                            "xp": min(max(int(item.get("xp", 15)), 5), 100)
                        }
                        cleaned_items.append(cleaned_item)
                items = cleaned_items[:3]
                
                # Store in cache
                if items:
                    store_in_cache(cache_key, items)
                
            except Exception as e:
                print(f"Task generation error: {e}")
                # Enhanced fallback with user context
                items = []
                categories = focus_areas[:3] if focus_areas else ["personal", "health", "learning"]
                
                for category in categories:
                    base_xp = {"easy": 10, "medium": 15, "hard": 25, "expert": 40}.get(difficulty, 15)
                    alignment = calculate_goal_alignment(category, active_goals)
                    
                    items.append({
                        "title": f"{category.title()} Progress",
                        "description": f"Make meaningful progress on your {category} goals",
                        "frequency": frequency,
                        "category": category,
                        "difficulty": difficulty,
                        "goal_alignment": alignment,
                        "xp": base_xp
                    })

    # Create tasks with enhanced properties
    tasks: List[Task] = []
    for item in items[:3]:
        try:
            # Calculate XP with alignment bonus
            base_xp = item.get("xp", 15)
            alignment = item.get("goal_alignment", 0.5)
            
            task = Task(
                title=item["title"],
                description=item["description"],
                frequency=frequency,
                category=item.get("category", "general"),
                difficulty=item.get("difficulty", difficulty),
                goal_alignment=alignment,
                xp=base_xp,
                created_at=datetime.utcnow()
            )
            
            # Calculate final XP with alignment bonus
            task.xp = task.calculate_xp_reward(base_xp)
            
            session.add(task)
            tasks.append(task)
        except Exception as e:
            print(f"Error creating task: {e}")
            continue
            
    if tasks:
        session.commit()
        for task in tasks:
            session.refresh(task)
    
    return tasks