import os
from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session
from .models import UserProfile, Task, Achievement, Goal  # Import models to register them


# Resolve a durable absolute path for SQLite DB
# Priority: explicit DATABASE_URL > SYSTEM_DB_PATH > default to server/system.db
_env_database_url = os.getenv("DATABASE_URL")
if _env_database_url:
    DATABASE_URL = _env_database_url
else:
    _db_path = os.getenv("SYSTEM_DB_PATH")
    if not _db_path:
        # Place DB alongside the server package (server/system.db)
        _root_dir = Path(__file__).resolve().parents[1]  # .../server
        _db_path = str(_root_dir / "system.db")
    # Ensure parent directory exists
    Path(_db_path).parent.mkdir(parents=True, exist_ok=True)
    DATABASE_URL = f"sqlite:///{_db_path}"

# Using synchronous engine for simplicity; FastAPI will offload blocking IO
engine = create_engine(DATABASE_URL, echo=False)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
