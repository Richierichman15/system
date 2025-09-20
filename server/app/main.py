from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import tasks, profile, health, ai, achievements, goals, auth
from .db import create_db_and_tables
import os
from dotenv import load_dotenv


def create_app() -> FastAPI:
    load_dotenv()
    app = FastAPI(title="Solo Leveling System API", version="0.1.0")

    # More permissive CORS during development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for development
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
    app.include_router(profile.router, prefix="/profile", tags=["profile"])
    app.include_router(ai.router, prefix="/ai", tags=["ai"])
    app.include_router(achievements.router, prefix="/achievements", tags=["achievements"])
    app.include_router(goals.router, prefix="/goals", tags=["goals"])
    app.include_router(auth.router, prefix="/auth", tags=["auth"])

    return app


app = create_app()


@app.on_event("startup")
def on_startup():
    create_db_and_tables()