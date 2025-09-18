from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select
from ..db import get_session
from ..models import Task
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
    
    print(f"DEBUG: Received goals: '{goals}', frequency: '{frequency}'")
    
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
                
                # Enhanced prompt for better task generation
                prompt = f"""Create 3 {frequency} tasks for goals: {goals}

Output must be valid JSON only:
[
{{"title":"First Task","description":"What to do","difficulty":"easy","category":"learning","xp":15}},
{{"title":"Second Task","description":"What to do","difficulty":"medium","category":"fitness","xp":25}},
{{"title":"Third Task","description":"What to do","difficulty":"hard","category":"personal","xp":40}}
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
    for item in items[:3]:  # Extra safety limit
        try:
            # Create task with new fields
            task = Task(
                title=item["title"],
                description=item["description"],
                frequency=frequency,
                difficulty=item.get("difficulty", "medium"),
                category=item.get("category", "general"),
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