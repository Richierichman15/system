import os
from sqlmodel import SQLModel, create_engine, Session


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./system.db")

# Using synchronous engine for simplicity; FastAPI will offload blocking IO
engine = create_engine(DATABASE_URL, echo=False)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
