#!/usr/bin/env python3
"""
Script to fix database datetime issues
"""
import os
import sys
sys.path.append('.')

from app.db import get_session, engine
from app.models import UserProfile, Task, Goal, Achievement
from sqlmodel import Session, select
from datetime import datetime

def fix_database():
    print("🔧 Fixing database datetime issues...")
    
    # Delete and recreate the database to avoid corrupted datetime fields
    db_path = "system.db"
    if os.path.exists(db_path):
        print(f"🗑️ Removing corrupted database: {db_path}")
        os.remove(db_path)
    
    # Recreate tables
    from app.db import create_db_and_tables
    create_db_and_tables()
    print("✅ Database recreated successfully")
    
    # Create a default user profile
    with Session(engine) as session:
        profile = UserProfile(
            id=1,
            name="Gitonga",
            xp=0,
            level=1,
            skill_points=0,
            goals="My goals are to improve my health, strengthen my mind, and build consistent habits.",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(profile)
        session.commit()
        print("✅ Created default user profile")

if __name__ == "__main__":
    fix_database()
