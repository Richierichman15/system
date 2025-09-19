from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select
from ..db import get_session
from ..models import Task
from ..services.ai_models import ai_service, TaskType
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


def background_ollama_request(prompt: str):
    """Make Ollama request in background to warm up the model"""
    try:
        ollama_url = "http://localhost:11434/api/generate"
        httpx.post(
            ollama_url,
            json={
                "model": "llama3.2:1b",  # Use the same model for consistency
                "prompt": prompt,
                "options": {
                    "temperature": 0.5,
                    "top_k": 10,
                    "top_p": 0.7,
                    "num_predict": 5  # Just generate a few tokens to warm up
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
    ten_seconds_ago = datetime.utcnow() - timedelta(seconds=10)
    recent_tasks = session.exec(
        select(Task).where(Task.created_at > ten_seconds_ago)
    ).all()
    
    if len(recent_tasks) > 5:  # Allow up to 5 tasks in 10 seconds
        raise HTTPException(
            status_code=429,
            detail="Please wait a moment before generating more tasks"
        )

    goals: str = payload.get("goals", "").strip()[:200]  # Limit input size
    frequency: str = payload.get("frequency", "daily")
    
    # Get user's profile goals and specific active goals
    from ..models import Goal, UserProfile
    profile_goals = ""
    active_goals = []
    
    try:
        # Get profile goals
        profile = session.get(UserProfile, 1)
        if profile and profile.goals:
            profile_goals = profile.goals
        
        # Get active specific goals
        active_goals = session.exec(
            select(Goal).where(Goal.user_id == 1, Goal.completed == False)
            .order_by(Goal.priority.desc(), Goal.created_at.desc())
        ).all()
        
        # Combine all goals for better task generation
        all_goals = []
        if profile_goals:
            all_goals.append(f"Profile Goals: {profile_goals}")
        if active_goals:
            goal_text = ", ".join([f"{goal.title} ({goal.category})" for goal in active_goals[:3]])  # Limit to top 3
            all_goals.append(f"Current Goals: {goal_text}")
        if goals:
            all_goals.append(f"Session Goals: {goals}")
            
        combined_goals = " | ".join(all_goals) if all_goals else goals
        
    except Exception as e:
        print(f"DEBUG: Error fetching goals: {e}")
        combined_goals = goals
    
    print(f"DEBUG: Combined goals for task generation: '{combined_goals}', frequency: '{frequency}'")
    
    # Check cache first
    cache_key = f"{goals}:{frequency}"
    cached_items = get_cached_tasks(cache_key)
    if cached_items:
        print(f"DEBUG: Using cached tasks for key: {cache_key}")
        items = cached_items
    else:
        # Generate tasks using AI
        if ollama is None:
            print("DEBUG: Ollama library not available, using fallback tasks")
            # Enhanced fallback tasks with difficulty and categories
            items = [
                {
                    "title": "Quick Study Session",
                    "description": "15 minutes focused learning",
                    "difficulty": "medium",
                    "category": "learning",
                    "xp": 20
                },
                {
                    "title": "Health Check",
                    "description": "5 minute stretching break",
                    "difficulty": "easy",
                    "category": "fitness",
                    "xp": 12
                },
                {
                    "title": "Daily Progress Review",
                    "description": "Reflect on progress toward goals",
                    "difficulty": "medium",
                    "category": "personal",
                    "xp": 18
                }
            ]
        else:
            try:
                print("DEBUG: Sending request to Ollama with llama3.2:1b...")
                # Use direct HTTP request to Ollama with optimized settings
                ollama_url = "http://localhost:11434/api/generate"
                
                # Enhanced prompt for better task generation with goal alignment
                prompt = f"""Create 1-2 {frequency} tasks specifically aligned with these goals: {combined_goals}

IMPORTANT: Create tasks that directly help achieve the stated goals. Focus on actionable steps that move the user closer to their specific objectives.

Output must be valid JSON only:
[
{{"title":"Goal-aligned Task","description":"Specific action that helps achieve the goals","difficulty":"medium","category":"work","xp":25}},
{{"title":"Second Goal Task","description":"Another action toward the goals","difficulty":"easy","category":"learning","xp":15}}
]

Categories: work, fitness, learning, social, personal, general
XP: easy=5-20, medium=20-35, hard=35-50
Return only JSON array."""
                
                response = httpx.post(
                    ollama_url,
                    json={
                        "model": "llama3.2:1b",  # Fast 1B model for task generation
                        "prompt": prompt,
                        "stream": False,  # Disable streaming for easier parsing
                        "options": {
                            "temperature": 0.7,
                            "top_k": 40,
                            "top_p": 0.9,
                            "num_ctx": 2048,  # Reasonable context for 1B model
                            "num_predict": 200,  # Enough for JSON response
                        }
                    },
                    timeout=15.0  # Reasonable timeout for 1B model
                )
                
                if not response.is_success:
                    print(f"DEBUG: Ollama error: {response.status_code} - {response.text}")
                    print("DEBUG: Falling back to default tasks due to Ollama error")
                    raise Exception("Ollama request failed")
                
                print(f"DEBUG: Ollama response status: {response.status_code}")
                    
                # Parse non-streaming response
                try:
                    response_data = response.json()
                    content = response_data.get("response", "")
                    print(f"DEBUG: Extracted response field: {content[:200]}...")
                except json.JSONDecodeError as e:
                    print(f"DEBUG: Failed to parse Ollama JSON response: {e}")
                    content = response.text
                    print(f"DEBUG: Using raw text response: {content[:200]}...")
                        
                print(f"DEBUG: Raw Ollama response content: {content[:500]}...")
                
                # Clean up the content for llama3.2
                content = content.strip()
                
                # Remove markdown code blocks
                if "```" in content:
                    parts = content.split("```")
                    for part in parts:
                        if part.strip().startswith("[") and part.strip().endswith("]"):
                            content = part.strip()
                            break
                
                # Find JSON array in the response
                start_idx = content.find("[")
                end_idx = content.rfind("]")
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    content = content[start_idx:end_idx + 1]
                
                print(f"DEBUG: Cleaned content for parsing: {content}")
                
                try:
                    print(f"DEBUG: Attempting to parse JSON: {content[:200]}...")
                    items = json.loads(content)[:3]  # Limit to 3 tasks max
                    print(f"DEBUG: Successfully parsed {len(items)} items from AI")
                except json.JSONDecodeError as e:
                    print(f"DEBUG: JSON decode error: {e}")
                    print(f"DEBUG: Full content was: {content}")
                    print("DEBUG: Using fallback tasks due to JSON parsing failure")
                    # Enhanced fallback tasks
                    items = [
                        {
                            "title": "Focus Session",
                            "description": "Complete a 25-minute focused work session",
                            "difficulty": "medium",
                            "category": "work",
                            "xp": 20
                        },
                        {
                            "title": "Skill Development",
                            "description": "Practice a new skill for 20 minutes",
                            "difficulty": "hard",
                            "category": "learning",
                            "xp": 30
                        },
                        {
                            "title": "Reflection Time",
                            "description": "Take 10 minutes to reflect on your progress",
                            "difficulty": "easy",
                            "category": "personal",
                            "xp": 12
                        }
                    ]
                
                # Enhanced validation with new fields
                cleaned_items = []
                valid_difficulties = ["easy", "medium", "hard", "expert"]
                valid_categories = ["work", "fitness", "learning", "social", "personal", "general"]
                
                for item in items:
                    if isinstance(item, dict) and "title" in item:
                        # Validate difficulty
                        difficulty = item.get("difficulty", "medium")
                        if difficulty not in valid_difficulties:
                            difficulty = "medium"
                            
                        # Validate category
                        category = item.get("category", "general")
                        if category not in valid_categories:
                            category = "general"
                        
                        # Clamp XP by difficulty ranges
                        ranges = {
                            "easy": (5, 20),
                            "medium": (20, 35),
                            "hard": (35, 50),
                            "expert": (50, 75),
                        }
                        xp_min, xp_max = ranges.get(difficulty, (20, 35))
                        raw_xp = int(item.get("xp", xp_min))
                        clamped_xp = min(max(raw_xp, xp_min), xp_max)

                        cleaned_item = {
                            "title": str(item.get("title", ""))[:50],
                            "description": str(item.get("description", ""))[:100],
                            "difficulty": difficulty,
                            "category": category,
                            "xp": clamped_xp
                        }
                        cleaned_items.append(cleaned_item)
                items = cleaned_items[:3]
                
                # Store in cache
                if items:
                    store_in_cache(cache_key, items)
                
            except Exception as e:
                print(f"DEBUG: Task generation error: {e}")
                print("DEBUG: Using final fallback tasks")
                # Enhanced final fallback tasks
                items = [
                    {
                        "title": "Focus Session",
                        "description": "Complete a 25-minute focused work session",
                        "difficulty": "medium",
                        "category": "work",
                        "xp": 20
                    },
                    {
                        "title": "Skill Development",
                        "description": "Practice a new skill for 20 minutes",
                        "difficulty": "hard",
                        "category": "learning",
                        "xp": 30
                    },
                    {
                        "title": "Reflection Time",
                        "description": "Take 10 minutes to reflect on your progress",
                        "difficulty": "easy",
                        "category": "personal",
                        "xp": 12
                    }
                ]

    # Create tasks with enhanced fields
    tasks: List[Task] = []
    for item in items[:2]:  # Limit to 1-2 tasks
        try:
            # Create task with new fields
            # Check if goals are job-related and adjust category accordingly
            job_keywords = ["job", "apply", "application", "career", "resume", "interview", "networking", "linkedin", "employment"]
            is_job_related = any(keyword in combined_goals.lower() for keyword in job_keywords)
            final_category = "work" if is_job_related else item.get("category", "general")
            
            task = Task(
                title=item["title"],
                description=item["description"],
                frequency=frequency,
                difficulty=item.get("difficulty", "medium"),
                category=final_category,
                xp=item["xp"],
                goal_alignment=0.0,  # Default goal alignment
                created_at=datetime.utcnow()
            )
            # Recalculate XP based on difficulty
            task.xp = task.calculate_xp_reward()
            session.add(task)
            tasks.append(task)
        except Exception as e:
            print(f"Error creating task: {e}")
            continue
            
    if tasks:  # Only commit if we have valid tasks
        print(f"DEBUG: Committing {len(tasks)} tasks to database")
        session.commit()
        for task in tasks:
            session.refresh(task)
        print(f"DEBUG: Successfully created tasks with IDs: {[task.id for task in tasks]}")
    else:
        print("DEBUG: No tasks to commit")
    
    return tasks


@router.post("/generate-advanced", response_model=List[Task])
async def generate_tasks_advanced(
    payload: dict, 
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    """
    Advanced AI task generation with specialized models and custom training
    """
    # Rate limiting
    ten_seconds_ago = datetime.utcnow() - timedelta(seconds=10)
    recent_tasks = session.exec(
        select(Task).where(Task.created_at > ten_seconds_ago)
    ).all()
    
    if len(recent_tasks) > 5:
        raise HTTPException(
            status_code=429,
            detail="Please wait a moment before generating more tasks"
        )

    goals: str = payload.get("goals", "").strip()[:200]
    frequency: str = payload.get("frequency", "daily")
    task_category: str = payload.get("category", "general")
    user_preferences: dict = payload.get("preferences", {})
    
    # Get user's profile goals and specific active goals for advanced generation
    from ..models import Goal, UserProfile
    profile_goals = ""
    active_goals = []
    
    try:
        # Get profile goals
        profile = session.get(UserProfile, 1)
        if profile and profile.goals:
            profile_goals = profile.goals
        
        # Get active specific goals
        active_goals = session.exec(
            select(Goal).where(Goal.user_id == 1, Goal.completed == False)
            .order_by(Goal.priority.desc(), Goal.created_at.desc())
        ).all()
        
        # Combine all goals for better task generation
        all_goals = []
        if profile_goals:
            all_goals.append(f"Profile Goals: {profile_goals}")
        if active_goals:
            goal_text = ", ".join([f"{goal.title} ({goal.category})" for goal in active_goals[:3]])  # Limit to top 3
            all_goals.append(f"Current Goals: {goal_text}")
        if goals:
            all_goals.append(f"Session Goals: {goals}")
            
        combined_goals = " | ".join(all_goals) if all_goals else goals
        
    except Exception as e:
        print(f"DEBUG: Error fetching goals for advanced generation: {e}")
        combined_goals = goals
    
    print(f"DEBUG: Advanced generation - combined goals: '{combined_goals}', category: '{task_category}'")
    
    # Check cache first with category-specific key
    cache_key = f"{goals}:{frequency}:{task_category}"
    cached_items = get_cached_tasks(cache_key)
    if cached_items:
        print(f"DEBUG: Using cached tasks for key: {cache_key}")
        items = cached_items
    else:
        try:
            # Use advanced AI service with combined goals
            items = await ai_service.generate_tasks_with_model(
                goals=combined_goals,
                frequency=frequency, 
                task_category=task_category,
                user_preferences=user_preferences
            )
            
            # Store in cache
            if items:
                store_in_cache(cache_key, items)
                
        except Exception as e:
            print(f"DEBUG: Advanced AI generation failed: {e}")
            # Fallback to original generation
            return await generate_tasks(payload, background_tasks, session)

    # Create tasks with enhanced fields
    tasks: List[Task] = []
    for item in items[:2]:  # Limit to 1-2 tasks
        try:
            task = Task(
                title=item["title"],
                description=item["description"],
                frequency=frequency,
                difficulty=item.get("difficulty", "medium"),
                category=task_category,  # Force use of selected category
                xp=item.get("xp", 20),
                goal_alignment=0.0,
                created_at=datetime.utcnow()
            )
            # Clamp XP to difficulty range
            task.xp = task.calculate_xp_reward()
            session.add(task)
            tasks.append(task)
        except Exception as e:
            print(f"DEBUG: Error creating advanced task: {e}")
            continue
            
    if tasks:
        print(f"DEBUG: Committing {len(tasks)} advanced tasks to database")
        session.commit()
        for task in tasks:
            session.refresh(task)
        print(f"DEBUG: Successfully created advanced tasks with IDs: {[task.id for task in tasks]}")
    else:
        print("DEBUG: No advanced tasks to commit")
    
    return tasks


@router.post("/feedback")
def submit_task_feedback(
    payload: dict,
    session: Session = Depends(get_session)
):
    """
    Submit feedback for task to improve AI generation
    """
    task_id = payload.get("task_id")
    rating = payload.get("rating", 3)  # 1-5 scale
    completed = payload.get("completed", False)
    completion_time = payload.get("completion_time")  # seconds
    
    # Get the task
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Get user's current goals for training context
    from ..models import UserProfile
    profile = session.get(UserProfile, 1)
    user_goals = profile.goals if profile else "No goals set"
    
    # Record feedback for AI learning
    ai_service.record_task_feedback(
        user_goals=user_goals,
        generated_task={
            "title": task.title,
            "description": task.description,
            "category": task.category,
            "difficulty": task.difficulty,
            "xp": task.xp
        },
        user_rating=rating,
        completed=completed,
        completion_time=completion_time
    )
    
    return {"message": "Feedback recorded successfully"}


@router.get("/models/stats")
def get_ai_model_stats():
    """
    Get statistics about AI model performance and usage
    """
    return ai_service.get_model_stats()


@router.get("/models/available")
def get_available_models():
    """
    Get list of available AI models and their specializations
    """
    return {
        "models": {
            "fast": {
                "name": "llama3.2:1b",
                "description": "Quick responses, good for simple tasks",
                "best_for": ["quick generation", "simple tasks"]
            },
            "balanced": {
                "name": "llama3.2:3b", 
                "description": "Good balance of speed and quality",
                "best_for": ["general tasks", "fitness", "health"]
            },
            "creative": {
                "name": "gemma2:2b",
                "description": "Better for creative and personal tasks",
                "best_for": ["creative projects", "personal goals", "hobbies"]
            },
            "analytical": {
                "name": "llama3.2:3b",
                "description": "Best for work and learning tasks",
                "best_for": ["work tasks", "learning goals", "skill development"]
            }
        },
        "task_specializations": {
            "fitness": "balanced",
            "learning": "analytical", 
            "work": "analytical",
            "personal": "creative",
            "creative": "creative",
            "social": "balanced",
            "health": "balanced"
        }
    }