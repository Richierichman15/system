import asyncio
import json
import sys
from typing import Any, Dict, List

try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent
except ModuleNotFoundError:
    sys.stderr.write("Missing dependency 'mcp'. Install with: pip install mcp\n")
    raise

# Reuse System's existing models and DB
from server.app.db import create_db_and_tables, engine
from server.app.models import Goal, Task, UserProfile
from sqlmodel import Session, select


server = Server("system-mcp")


def _ensure_profile(session: Session) -> UserProfile:
    profile = session.get(UserProfile, 1)
    if not profile:
        profile = UserProfile(id=1)
        session.add(profile)
        session.flush()
    return profile


def _json_schema_object(properties: Dict[str, Any], required: List[str] | None = None) -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": required or [],
        "additionalProperties": False,
    }


@server.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="system.add_goal",
            description="Add a goal with a numeric target into System's database.",
            inputSchema=_json_schema_object(
                {
                    "title": {"type": "string", "description": "Goal title"},
                    "target": {"type": "number", "description": "Numeric target for the goal"},
                },
                required=["title", "target"],
            ),
        ),
        Tool(
            name="system.check_progress",
            description="Check current progress (0.0-1.0) toward a goal by title.",
            inputSchema=_json_schema_object(
                {"title": {"type": "string", "description": "Goal title"}},
                required=["title"],
            ),
        ),
        Tool(
            name="system.get_status",
            description="Get a summary of XP, active quests, and goals.",
            inputSchema={"type": "object", "properties": {}, "additionalProperties": False},
        ),
    ]


def _parse_goal_description_for_target(desc: str | None) -> Any:
    if not desc:
        return None
    try:
        data = json.loads(desc)
        if isinstance(data, dict) and "target" in data:
            return data["target"]
    except Exception:
        # Not JSON; try simple pattern like "target: 12000"
        if "target:" in desc:
            try:
                return float(desc.split("target:")[-1].strip().split()[0])
            except Exception:
                return None
    return None


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    # Ensure DB is initialized for every call (idempotent)
    create_db_and_tables()

    if name == "system.add_goal":
        title = str(arguments.get("title", "")).strip()
        if not title:
            return [TextContent(type="text", text=json.dumps({"error": "title is required"}))]
        try:
            target = float(arguments.get("target"))
        except Exception:
            return [TextContent(type="text", text=json.dumps({"error": "target must be a number"}))]

        with Session(engine) as session:
            _ensure_profile(session)

            # Store target inside description as JSON to avoid schema changes
            goal = Goal(
                user_id=1,
                title=title,
                category="financial",
                description=json.dumps({"target": target}),
                progress=0.0,
                completed=False,
            )
            session.add(goal)
            session.commit()
            session.refresh(goal)

            response = {
                "ok": True,
                "goal": {
                    "id": goal.id,
                    "title": goal.title,
                    "category": goal.category,
                    "target": target,
                    "progress": goal.progress,
                    "completed": goal.completed,
                },
            }
            return [TextContent(type="text", text=json.dumps(response))]

    if name == "system.check_progress":
        title = str(arguments.get("title", "")).strip()
        if not title:
            return [TextContent(type="text", text=json.dumps({"error": "title is required"}))]

        with Session(engine) as session:
            goal = session.exec(
                select(Goal).where(Goal.user_id == 1, Goal.title == title).order_by(Goal.created_at.desc())
            ).first()

            if not goal:
                return [TextContent(type="text", text=json.dumps({"error": "goal not found", "title": title}))]

            target = _parse_goal_description_for_target(goal.description)
            response = {
                "ok": True,
                "title": goal.title,
                "progress": goal.progress,
                "completed": goal.completed,
                "target": target,
            }
            return [TextContent(type="text", text=json.dumps(response))]

    if name == "system.get_status":
        with Session(engine) as session:
            profile = _ensure_profile(session)

            # Active quests = active, not completed tasks
            active_tasks = session.exec(
                select(Task).where(Task.active == True, Task.completed == False)  # noqa: E712
            ).all()

            # Active goals = not completed
            active_goals = session.exec(
                select(Goal).where(Goal.user_id == 1, Goal.completed == False)  # noqa: E712
            ).all()

            goals_summary = [
                {
                    "id": g.id,
                    "title": g.title,
                    "progress": g.progress,
                    "completed": g.completed,
                }
                for g in active_goals
            ]

            tasks_summary = [
                {
                    "id": t.id,
                    "title": t.title,
                    "category": t.category,
                    "difficulty": t.difficulty,
                    "xp": t.xp,
                }
                for t in active_tasks[:10]
            ]

            # Compute progress to next level using model helper
            profile_level = profile.calculate_level()
            profile.level = profile_level  # keep in sync
            progress_ratio = profile.progress_to_next_level()

            response = {
                "ok": True,
                "xp": profile.xp,
                "level": profile.level,
                "progress_to_next_level": progress_ratio,
                "active_quests_count": len(active_tasks),
                "active_goals_count": len(active_goals),
                "active_quests_sample": tasks_summary,
                "active_goals": goals_summary,
            }
            return [TextContent(type="text", text=json.dumps(response))]

    return [TextContent(type="text", text=json.dumps({"error": f"unknown tool: {name}"}))]


def main() -> None:
    # Keep for compatibility if invoked programmatically
    create_db_and_tables()
    import asyncio as _asyncio
    _asyncio.run(run_stdio())


async def run_stdio() -> None:
    """Start MCP stdio server using the current SDK's stdio transport."""
    # Import here to avoid hard dependency during module import
    from mcp.server.stdio import stdio_server

    create_db_and_tables()
    async with stdio_server() as (read_stream, write_stream):
        init = server.create_initialization_options()
        await server.run(read_stream, write_stream, init)


# Attach method for compatibility with the requested startup snippet
setattr(server, "run_stdio", run_stdio)


if __name__ == "__main__":
    import asyncio as _asyncio
    _asyncio.run(server.run_stdio())
