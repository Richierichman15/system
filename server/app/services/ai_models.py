"""
Advanced AI Models Service
Handles multiple AI models, local processing, and custom training
"""

import json
import httpx
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime, timedelta
import sqlite3
import os
from pathlib import Path


class TaskType(Enum):
    FITNESS = "fitness"
    LEARNING = "learning"
    WORK = "work"
    PERSONAL = "personal"
    CREATIVE = "creative"
    SOCIAL = "social"
    HEALTH = "health"


class ModelType(Enum):
    FAST = "fast"           # Quick responses, lower quality
    BALANCED = "balanced"   # Good balance of speed/quality  
    CREATIVE = "creative"   # Better for creative/personal tasks
    ANALYTICAL = "analytical" # Better for work/learning tasks


class AIModelService:
    def __init__(self):
        self.models = {
            ModelType.FAST: "llama3.2:1b",
            ModelType.BALANCED: "llama3.2:3b", 
            ModelType.CREATIVE: "gemma2:2b",
            ModelType.ANALYTICAL: "llama3.2:3b"
        }
        
        # Model specializations for different task types
        self.task_model_mapping = {
            TaskType.FITNESS: ModelType.BALANCED,
            TaskType.LEARNING: ModelType.ANALYTICAL,
            TaskType.WORK: ModelType.ANALYTICAL,
            TaskType.PERSONAL: ModelType.CREATIVE,
            TaskType.CREATIVE: ModelType.CREATIVE,
            TaskType.SOCIAL: ModelType.BALANCED,
            TaskType.HEALTH: ModelType.BALANCED
        }
        
        # Custom training data storage
        self.training_db_path = "user_training_data.db"
        self._init_training_db()
        
    def _init_training_db(self):
        """Initialize SQLite database for custom training data"""
        conn = sqlite3.connect(self.training_db_path)
        cursor = conn.cursor()
        
        # Store user interactions for learning
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_goals TEXT,
                generated_task TEXT,
                task_category TEXT,
                user_rating INTEGER,  -- 1-5 rating
                completion_status BOOLEAN,
                completion_time INTEGER,  -- seconds taken
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Store successful task patterns
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT,  -- time_of_day, difficulty_preference, etc.
                pattern_value TEXT,
                task_category TEXT,
                success_rate FLOAT,
                usage_count INTEGER DEFAULT 1,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def get_optimal_model(self, task_category: str, user_preferences: Dict = None) -> str:
        """Select the best model based on task type and user preferences"""
        try:
            task_type = TaskType(task_category.lower())
        except ValueError:
            task_type = TaskType.PERSONAL  # Default fallback
            
        # Check user preferences for model type
        if user_preferences and "preferred_model_type" in user_preferences:
            model_type = ModelType(user_preferences["preferred_model_type"])
        else:
            model_type = self.task_model_mapping.get(task_type, ModelType.BALANCED)
            
        return self.models[model_type]
    
    def get_custom_prompt(self, goals: str, task_category: str, frequency: str) -> str:
        """Generate a custom prompt based on learned user patterns"""
        base_prompt = f"""Create 3 {frequency} tasks for goals: {goals}

Output must be valid JSON only:
[
{{"title":"Task Name","description":"What to do","difficulty":"easy","category":"{task_category}","xp":15}},
{{"title":"Second Task","description":"What to do","difficulty":"medium","category":"{task_category}","xp":25}},
{{"title":"Third Task","description":"What to do","difficulty":"hard","category":"{task_category}","xp":40}}
]

Categories: work, fitness, learning, social, personal, general
XP: easy=5-20, medium=20-35, hard=35-50"""

        # Add learned patterns
        patterns = self._get_user_patterns(task_category)
        if patterns:
            base_prompt += f"\n\nUser preferences learned from past completions:\n{patterns}"
            
        return base_prompt
    
    def _get_user_patterns(self, task_category: str) -> str:
        """Get learned patterns for this user and category"""
        conn = sqlite3.connect(self.training_db_path)
        cursor = conn.cursor()
        
        # Get successful patterns for this category
        cursor.execute('''
            SELECT pattern_type, pattern_value, success_rate 
            FROM task_patterns 
            WHERE task_category = ? AND success_rate > 0.7
            ORDER BY success_rate DESC, usage_count DESC
            LIMIT 3
        ''', (task_category,))
        
        patterns = cursor.fetchall()
        conn.close()
        
        if not patterns:
            return ""
            
        pattern_text = ""
        for pattern_type, pattern_value, success_rate in patterns:
            pattern_text += f"- {pattern_type}: {pattern_value} (success rate: {success_rate:.1%})\n"
            
        return pattern_text
    
    async def generate_tasks_with_model(
        self, 
        goals: str, 
        frequency: str, 
        task_category: str = "general",
        user_preferences: Dict = None
    ) -> List[Dict]:
        """Generate tasks using the optimal model for the task type"""
        
        # Select optimal model
        model_name = self.get_optimal_model(task_category, user_preferences)
        
        # Get custom prompt with learned patterns
        prompt = self.get_custom_prompt(goals, task_category, frequency)
        
        print(f"DEBUG: Using model {model_name} for {task_category} tasks")
        
        try:
            # Make request to Ollama
            ollama_url = "http://localhost:11434/api/generate"
            
            response = await httpx.AsyncClient().post(
                ollama_url,
                json={
                    "model": model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.8 if task_category in ["creative", "personal"] else 0.6,
                        "top_k": 40,
                        "top_p": 0.9,
                        "num_ctx": 2048,
                        "num_predict": 250,
                    }
                },
                timeout=20.0
            )
            
            if not response.is_success:
                raise Exception(f"Model {model_name} request failed: {response.status_code}")
                
            response_data = response.json()
            content = response_data.get("response", "")
            
            # Parse JSON response
            content = self._clean_json_response(content)
            tasks = json.loads(content)
            
            print(f"DEBUG: Successfully generated {len(tasks)} tasks with {model_name}")
            return tasks[:3]  # Limit to 3 tasks
            
        except Exception as e:
            print(f"DEBUG: Error with model {model_name}: {e}")
            # Fallback to fast model
            return await self._fallback_generation(goals, frequency, task_category)
    
    def _clean_json_response(self, content: str) -> str:
        """Clean and extract JSON from model response"""
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
        
        return content
    
    async def _fallback_generation(self, goals: str, frequency: str, task_category: str) -> List[Dict]:
        """Fallback to simple fast model if specialized model fails"""
        try:
            return await self.generate_tasks_with_model(
                goals, frequency, task_category, {"preferred_model_type": "fast"}
            )
        except:
            # Final fallback to hardcoded tasks
            return [
                {
                    "title": f"Quick {task_category.title()} Task",
                    "description": f"Complete a 15-minute {task_category} activity",
                    "difficulty": "medium",
                    "category": task_category,
                    "xp": 20
                }
            ]
    
    def record_task_feedback(
        self, 
        user_goals: str, 
        generated_task: Dict, 
        user_rating: int, 
        completed: bool,
        completion_time: Optional[int] = None
    ):
        """Record user feedback for custom training"""
        conn = sqlite3.connect(self.training_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO task_feedback 
            (user_goals, generated_task, task_category, user_rating, completion_status, completion_time)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user_goals,
            json.dumps(generated_task),
            generated_task.get("category", "general"),
            user_rating,
            completed,
            completion_time
        ))
        
        conn.commit()
        conn.close()
        
        # Update patterns based on feedback
        if user_rating >= 4 and completed:  # Good feedback
            self._update_success_patterns(generated_task)
    
    def _update_success_patterns(self, task: Dict):
        """Update learned patterns based on successful tasks"""
        conn = sqlite3.connect(self.training_db_path)
        cursor = conn.cursor()
        
        category = task.get("category", "general")
        difficulty = task.get("difficulty", "medium")
        
        # Update difficulty preference pattern
        cursor.execute('''
            INSERT OR REPLACE INTO task_patterns 
            (pattern_type, pattern_value, task_category, success_rate, usage_count)
            VALUES (?, ?, ?, 
                COALESCE((SELECT success_rate FROM task_patterns 
                         WHERE pattern_type = ? AND pattern_value = ? AND task_category = ?), 0.5) + 0.1,
                COALESCE((SELECT usage_count FROM task_patterns 
                         WHERE pattern_type = ? AND pattern_value = ? AND task_category = ?), 0) + 1
            )
        ''', (
            "difficulty_preference", difficulty, category,
            "difficulty_preference", difficulty, category,
            "difficulty_preference", difficulty, category
        ))
        
        conn.commit()
        conn.close()
    
    def get_model_stats(self) -> Dict:
        """Get statistics about model usage and performance"""
        conn = sqlite3.connect(self.training_db_path)
        cursor = conn.cursor()
        
        # Get completion rates by category
        cursor.execute('''
            SELECT task_category, 
                   AVG(CAST(completion_status AS FLOAT)) as completion_rate,
                   AVG(user_rating) as avg_rating,
                   COUNT(*) as total_tasks
            FROM task_feedback 
            GROUP BY task_category
        ''')
        
        category_stats = {}
        for category, completion_rate, avg_rating, total_tasks in cursor.fetchall():
            category_stats[category] = {
                "completion_rate": completion_rate or 0,
                "avg_rating": avg_rating or 0,
                "total_tasks": total_tasks
            }
        
        conn.close()
        
        return {
            "available_models": list(self.models.keys()),
            "category_performance": category_stats,
            "total_feedback_entries": sum(stats["total_tasks"] for stats in category_stats.values())
        }


# Global instance
ai_service = AIModelService()
