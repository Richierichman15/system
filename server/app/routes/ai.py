from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ..db import get_session
from ..models import Task
from typing import List
import os
import json
from datetime import datetime, timedelta
import httpx

try:
    import ollama
except Exception:  # pragma: no cover
    ollama = None


router = APIRouter()


@router.post("/generate", response_model=List[Task])
def generate_tasks(payload: dict, session: Session = Depends(get_session)):
    """
    Generate tasks using Ollama based on user's goals and preferences.
    Expected payload keys: goals (str), frequency (str: daily|weekly|monthly)
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
    
    # Use shorter prompt for quicker generation
    prompt = (
        "Generate 3 tasks as JSON array for these goals:\n"
        f"Goals: {goals}\n"
        f"Frequency: {frequency}\n"
        'Format: [{"title": "Task Name", "description": "Action", "frequency": "daily", "xp": 20}]\n'
        "Keep titles under 50 chars, descriptions under 100 chars, xp between 10-30."
    )

    items: List[dict]
    if ollama is None:
        print("Ollama not available, using fallback tasks")
        # Lightweight fallback tasks
        items = [
            {
                "title": "Quick Study Session",
                "description": "15 minutes focused learning",
                "frequency": frequency,
                "xp": 15
            },
            {
                "title": "Health Check",
                "description": "5 minute stretching break",
                "frequency": frequency,
                "xp": 10
            }
        ]
    else:
        try:
            print("Sending request to Ollama...")
            # Use direct HTTP request to Ollama
            ollama_url = "http://localhost:11434/api/generate"
            response = httpx.post(
                ollama_url,
                json={
                    "model": "llama3:8b-instruct-q4_0",
                    "prompt": f"Return only a JSON array of tasks: {prompt}",
                    "options": {
                        "temperature": 0.5,
                        "top_k": 10,
                        "top_p": 0.7,
                    }
                },
                timeout=30.0  # 30 second timeout
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
                items = []
            
            # Simple validation without excessive processing
            cleaned_items = []
            for item in items:
                if isinstance(item, dict) and "title" in item:
                    cleaned_item = {
                        "title": str(item.get("title", ""))[:50],
                        "description": str(item.get("description", ""))[:100],
                        "frequency": frequency,
                        "xp": min(max(int(item.get("xp", 15)), 10), 30)
                    }
                    cleaned_items.append(cleaned_item)
            items = cleaned_items[:3]
            
        except Exception as e:
            print(f"Task generation error: {e}")
            # Return fallback tasks instead of failing
            items = [
                {
                    "title": "Daily Progress",
                    "description": "Make progress on your goals",
                    "frequency": frequency,
                    "xp": 15
                },
                {
                    "title": "Quick Win",
                    "description": "Complete one small task toward your goal",
                    "frequency": frequency,
                    "xp": 10
                }
            ]

    # Limit number of tasks created
    tasks: List[Task] = []
    for item in items[:3]:  # Extra safety limit
        try:
            task = Task(
                title=item["title"],
                description=item["description"],
                frequency=frequency,
                xp=item["xp"],
                created_at=datetime.utcnow()
            )
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