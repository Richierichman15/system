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
                "model": "tinyllama:latest",  # Use the same model for consistency
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
    one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
    recent_tasks = session.exec(
        select(Task).where(Task.created_at > one_minute_ago)
    ).all()
    
    if len(recent_tasks) > 0:
        raise HTTPException(
            status_code=429,
            detail="Please wait a moment before generating more tasks"
        )

    goals: str = payload.get("goals", "").strip()[:200]  # Limit input size
    frequency: str = payload.get("frequency", "daily")
    
    # Check cache first
    cache_key = f"{goals}:{frequency}"
    cached_items = get_cached_tasks(cache_key)
    if cached_items:
        print("Using cached tasks")
        items = cached_items
    else:
        # Generate tasks using AI
        if ollama is None:
            print("Ollama not available, using fallback tasks")
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
                print("Sending request to Ollama...")
                # Use direct HTTP request to Ollama with optimized settings
                ollama_url = "http://localhost:11434/api/generate"
                
                # Enhanced prompt for better task generation
                prompt = (
                    f"Create 3 {frequency} tasks as JSON array for goals: {goals}\n"
                    "Format: [{\"title\":\"Task Name\",\"description\":\"What to do\",\"difficulty\":\"easy|medium|hard\",\"category\":\"work|fitness|learning|social|personal|general\",\"xp\":15}]\n"
                    "Easy tasks: 10-15 XP, Medium: 15-25 XP, Hard: 25-40 XP\n"
                    "Match category to goal type. Vary difficulty levels."
                )
                
                response = httpx.post(
                    ollama_url,
                    json={
                        "model": "tinyllama:latest",  # Tiny model for speed
                        "prompt": f"Return only a JSON array of tasks: {prompt}",
                        "options": {
                            "temperature": 0.5,
                            "top_k": 10,
                            "top_p": 0.7,
                            "num_ctx": 256,  # Even smaller context
                            "num_predict": 150,  # Limit output size
                            "mirostat": 1,  # Enable adaptive sampling
                            "mirostat_eta": 0.1,  # Lower is faster
                            "mirostat_tau": 5.0  # Lower is more deterministic
                        }
                    },
                    timeout=10.0  # Even shorter timeout
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
                    items = json.loads(content)[:3]  # Limit to 3 tasks max
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    print(f"Content was: {content}")
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
                        
                        cleaned_item = {
                            "title": str(item.get("title", ""))[:50],
                            "description": str(item.get("description", ""))[:100],
                            "difficulty": difficulty,
                            "category": category,
                            "xp": min(max(int(item.get("xp", 15)), 10), 50)
                        }
                        cleaned_items.append(cleaned_item)
                items = cleaned_items[:3]
                
                # Store in cache
                if items:
                    store_in_cache(cache_key, items)
                
            except Exception as e:
                print(f"Task generation error: {e}")
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
        session.commit()
        for task in tasks:
            session.refresh(task)
    
    return tasks