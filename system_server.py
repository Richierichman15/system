import asyncio
import json
import sys
from typing import Any, Dict, List
from datetime import datetime

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


def _task_to_dict(t: Task) -> Dict[str, Any]:
    def ts(dt):
        return dt.isoformat() if dt else None
    return {
        "id": t.id,
        "title": t.title,
        "description": t.description,
        "frequency": t.frequency,
        "difficulty": t.difficulty,
        "category": t.category,
        "xp": t.xp,
        "is_recurring": t.is_recurring,
        "recurring_interval": t.recurring_interval,
        "active": t.active,
        "completed": t.completed,
        "completed_at": ts(t.completed_at),
        "created_at": ts(t.created_at),
        "updated_at": ts(t.updated_at),
    }


@server.list_tools()
async def list_tools() -> List[Tool]:
    return [
        # Preferred "quest" tools
        Tool(
            name="system.create_quest",
            description="Create a new quest (task) visible in the System UI.",
            inputSchema=_json_schema_object(
                {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "frequency": {"type": "string", "enum": ["daily", "weekly", "monthly"], "default": "daily"},
                    "difficulty": {"type": "string", "enum": ["easy", "medium", "hard", "expert"], "default": "medium"},
                    "category": {"type": "string", "enum": [
                        "work", "fitness", "learning", "social", "personal", "general", "career", "health", "financial", "relationships"
                    ], "default": "general"},
                    "xp": {"type": "number", "description": "Optional XP; will be clamped by difficulty."},
                    "is_recurring": {"type": "boolean", "default": False},
                    "recurring_interval": {"type": "integer", "minimum": 1},
                },
                required=["title"],
            ),
        ),
        Tool(
            name="system.get_quest",
            description="Fetch a quest by id with full details.",
            inputSchema=_json_schema_object({"id": {"type": "integer"}}, required=["id"]),
        ),
        Tool(
            name="system.list_quests",
            description="List recent quests with optional filters.",
            inputSchema=_json_schema_object(
                {
                    "completed": {"type": "boolean"},
                    "category": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 10},
                },
                required=[],
            ),
        ),
        Tool(
            name="system.complete_quest",
            description="Mark a quest as completed and award XP using backend logic.",
            inputSchema=_json_schema_object({"id": {"type": "integer"}}, required=["id"]),
        ),
        Tool(
            name="system.set_quest_completed",
            description="Set a quest's completed state. If true, awards XP; if false, un-completes.",
            inputSchema=_json_schema_object(
                {"id": {"type": "integer"}, "completed": {"type": "boolean"}}, required=["id", "completed"]
            ),
        ),
        Tool(
            name="system.toggle_quest_active",
            description="Toggle a quest's active state (cannot activate a completed quest).",
            inputSchema=_json_schema_object(
                {"id": {"type": "integer"}, "active": {"type": "boolean"}}, required=["id", "active"]
            ),
        ),
        Tool(
            name="system.update_quest",
            description="Update quest fields; XP clamps if difficulty/xp change.",
            inputSchema=_json_schema_object(
                {
                    "id": {"type": "integer"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "frequency": {"type": "string", "enum": ["daily", "weekly", "monthly"]},
                    "difficulty": {"type": "string", "enum": ["easy", "medium", "hard", "expert"]},
                    "category": {"type": "string"},
                    "xp": {"type": "number"},
                    "is_recurring": {"type": "boolean"},
                    "recurring_interval": {"type": "integer", "minimum": 1},
                    "active": {"type": "boolean"}
                },
                required=["id"],
            ),
        ),
        Tool(
            name="system.delete_quest",
            description="Delete a quest by id.",
            inputSchema=_json_schema_object({"id": {"type": "integer"}}, required=["id"]),
        ),

        # Existing goal tool
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
        # Legacy "task" tools (kept for compatibility)
        Tool(
            name="system.create_task",
            description="[Deprecated] Use system.create_quest. Create a new quest/task.",
            inputSchema=_json_schema_object(
                {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "frequency": {"type": "string", "enum": ["daily", "weekly", "monthly"], "default": "daily"},
                    "difficulty": {"type": "string", "enum": ["easy", "medium", "hard", "expert"], "default": "medium"},
                    "category": {"type": "string", "enum": [
                        "work", "fitness", "learning", "social", "personal", "general", "career", "health", "financial", "relationships"
                    ], "default": "general"},
                    "xp": {"type": "number", "description": "Optional XP; will be clamped by difficulty."},
                    "is_recurring": {"type": "boolean", "default": False},
                    "recurring_interval": {"type": "integer", "minimum": 1},
                },
                required=["title"],
            ),
        ),
        Tool(
            name="system.get_task",
            description="[Deprecated] Use system.get_quest. Fetch a task by id.",
            inputSchema=_json_schema_object({"id": {"type": "integer"}}, required=["id"]),
        ),
        Tool(
            name="system.list_tasks",
            description="[Deprecated] Use system.list_quests. List recent tasks.",
            inputSchema=_json_schema_object(
                {
                    "completed": {"type": "boolean"},
                    "category": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 10},
                },
                required=[],
            ),
        ),
        Tool(
            name="system.complete_task",
            description="[Deprecated] Use system.complete_quest. Complete a task.",
            inputSchema=_json_schema_object({"id": {"type": "integer"}}, required=["id"]),
        ),
        Tool(
            name="system.set_task_completed",
            description="[Deprecated] Use system.set_quest_completed. Set task completed state.",
            inputSchema=_json_schema_object(
                {"id": {"type": "integer"}, "completed": {"type": "boolean"}}, required=["id", "completed"]
            ),
        ),
        Tool(
            name="system.toggle_task_active",
            description="[Deprecated] Use system.toggle_quest_active. Toggle a task active flag.",
            inputSchema=_json_schema_object(
                {"id": {"type": "integer"}, "active": {"type": "boolean"}}, required=["id", "active"]
            ),
        ),
        Tool(
            name="system.update_task",
            description="[Deprecated] Use system.update_quest. Update a task.",
            inputSchema=_json_schema_object(
                {
                    "id": {"type": "integer"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "frequency": {"type": "string", "enum": ["daily", "weekly", "monthly"]},
                    "difficulty": {"type": "string", "enum": ["easy", "medium", "hard", "expert"]},
                    "category": {"type": "string"},
                    "xp": {"type": "number"},
                    "is_recurring": {"type": "boolean"},
                    "recurring_interval": {"type": "integer", "minimum": 1},
                    "active": {"type": "boolean"}
                },
                required=["id"],
            ),
        ),
        Tool(
            name="system.delete_task",
            description="[Deprecated] Use system.delete_quest. Delete a task.",
            inputSchema=_json_schema_object({"id": {"type": "integer"}}, required=["id"]),
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

    if name in ("system.create_task", "system.create_quest"):
        title = str(arguments.get("title", "")).strip()
        if not title:
            return [TextContent(type="text", text=json.dumps({"error": "title is required"}))]

        description = arguments.get("description")
        frequency = (arguments.get("frequency") or "daily").strip()
        difficulty = (arguments.get("difficulty") or "medium").strip()
        category = (arguments.get("category") or "general").strip()
        xp = arguments.get("xp")
        is_recurring = bool(arguments.get("is_recurring", False))
        recurring_interval = arguments.get("recurring_interval")

        with Session(engine) as session:
            # Build task and clamp XP via model helper
            task = Task(
                title=title,
                description=description,
                frequency=frequency,
                difficulty=difficulty,
                category=category,
                xp=int(xp) if xp is not None else 0,
                is_recurring=is_recurring,
                recurring_interval=int(recurring_interval) if recurring_interval else None,
                active=True,
                completed=False,
            )
            task.xp = task.calculate_xp_reward()
            session.add(task)
            session.commit()
            session.refresh(task)

            response = {
                "ok": True,
                "task": {
                    "id": task.id,
                    "title": task.title,
                    "category": task.category,
                    "difficulty": task.difficulty,
                    "xp": task.xp,
                    "active": task.active,
                    "completed": task.completed,
                },
            }
            return [TextContent(type="text", text=json.dumps(response))]

    if name in ("system.list_tasks", "system.list_quests"):
        completed = arguments.get("completed")
        category = arguments.get("category")
        limit = int(arguments.get("limit") or 10)
        limit = max(1, min(limit, 100))

        with Session(engine) as session:
            query = select(Task).order_by(Task.created_at.desc())
            if category:
                query = query.where(Task.category == category)
            if completed is not None:
                query = query.where(Task.completed == bool(completed))
            tasks = session.exec(query).all()[:limit]
            payload = [
                {
                    "id": t.id,
                    "title": t.title,
                    "category": t.category,
                    "difficulty": t.difficulty,
                    "xp": t.xp,
                    "active": t.active,
                    "completed": t.completed,
                }
                for t in tasks
            ]
            return [TextContent(type="text", text=json.dumps({"ok": True, "tasks": payload}))]

    if name in ("system.complete_task", "system.complete_quest"):
        try:
            task_id = int(arguments.get("id"))
        except Exception:
            return [TextContent(type="text", text=json.dumps({"error": "id must be an integer"}))]

        # Reuse backend route logic for XP/achievements/goal updates
        from server.app.routes.tasks import complete_task as route_complete_task

        with Session(engine) as session:
            result = route_complete_task(task_id, session)
            task = result.get("task")
            profile = result.get("profile")
            response = {
                "ok": True,
                "task": {
                    "id": task.id,
                    "title": task.title,
                    "completed": task.completed,
                    "xp": task.xp,
                },
                "profile": {"xp": profile.xp, "level": profile.level},
                "xp_gained": result.get("xp_gained"),
                "level_up": result.get("level_up"),
            }
            return [TextContent(type="text", text=json.dumps(response))]

    if name in ("system.set_task_completed", "system.set_quest_completed"):
        try:
            task_id = int(arguments.get("id"))
        except Exception:
            return [TextContent(type="text", text=json.dumps({"error": "id must be an integer"}))]
        completed_flag = bool(arguments.get("completed", True))

        if completed_flag:
            # Delegate to complete_task logic
            return await call_tool("system.complete_task", {"id": task_id})
        else:
            with Session(engine) as session:
                task = session.get(Task, task_id)
                if not task:
                    return [TextContent(type="text", text=json.dumps({"error": "task not found", "id": task_id}))]
                task.completed = False
                task.completed_at = None
                session.add(task)
                session.commit()
                session.refresh(task)
                return [TextContent(type="text", text=json.dumps({
                    "ok": True,
                    "task": {"id": task.id, "title": task.title, "completed": task.completed}
                }))]

    if name in ("system.get_task", "system.get_quest"):
        try:
            task_id = int(arguments.get("id"))
        except Exception:
            return [TextContent(type="text", text=json.dumps({"error": "id must be an integer"}))]

        with Session(engine) as session:
            task = session.get(Task, task_id)
            if not task:
                return [TextContent(type="text", text=json.dumps({"error": "task not found", "id": task_id}))]
            return [TextContent(type="text", text=json.dumps({"ok": True, "task": _task_to_dict(task)}))]

    if name in ("system.delete_task", "system.delete_quest"):
        try:
            task_id = int(arguments.get("id"))
        except Exception:
            return [TextContent(type="text", text=json.dumps({"error": "id must be an integer"}))]

        with Session(engine) as session:
            task = session.get(Task, task_id)
            if not task:
                return [TextContent(type="text", text=json.dumps({"error": "task not found", "id": task_id}))]
            title = task.title
            session.delete(task)
            session.commit()
            return [TextContent(type="text", text=json.dumps({"ok": True, "deleted": {"id": task_id, "title": title}}))]

    if name in ("system.toggle_task_active", "system.toggle_quest_active"):
        try:
            task_id = int(arguments.get("id"))
        except Exception:
            return [TextContent(type="text", text=json.dumps({"error": "id must be an integer"}))]
        desired_active = bool(arguments.get("active", True))

        with Session(engine) as session:
            task = session.get(Task, task_id)
            if not task:
                return [TextContent(type="text", text=json.dumps({"error": "task not found", "id": task_id}))]
            if desired_active and task.completed:
                return [TextContent(type="text", text=json.dumps({"error": "cannot activate a completed task"}))]

            task.active = desired_active
            task.updated_at = datetime.utcnow()
            session.add(task)
            session.commit()
            session.refresh(task)
            return [TextContent(type="text", text=json.dumps({
                "ok": True,
                "task": {"id": task.id, "title": task.title, "active": task.active, "completed": task.completed}
            }))]

    if name in ("system.update_task", "system.update_quest"):
        try:
            task_id = int(arguments.get("id"))
        except Exception:
            return [TextContent(type="text", text=json.dumps({"error": "id must be an integer"}))]

        editable_fields = {
            "title", "description", "frequency", "difficulty", "category",
            "xp", "is_recurring", "recurring_interval", "active"
        }
        payload = {k: v for k, v in arguments.items() if k in editable_fields}

        with Session(engine) as session:
            task = session.get(Task, task_id)
            if not task:
                return [TextContent(type="text", text=json.dumps({"error": "task not found", "id": task_id}))]

            # Apply updates
            for key, value in payload.items():
                if key == "recurring_interval" and value is not None:
                    try:
                        value = int(value)
                    except Exception:
                        return [TextContent(type="text", text=json.dumps({"error": "recurring_interval must be an integer"}))]
                if key == "xp" and value is not None:
                    try:
                        value = int(value)
                    except Exception:
                        return [TextContent(type="text", text=json.dumps({"error": "xp must be a number"}))]
                if key == "active" and value and task.completed:
                    return [TextContent(type="text", text=json.dumps({"error": "cannot activate a completed task"}))]
                setattr(task, key, value)

            # Recalculate/clamp XP if difficulty or xp changed
            if ("difficulty" in payload) or ("xp" in payload):
                task.xp = task.calculate_xp_reward()

            task.updated_at = datetime.utcnow()
            session.add(task)
            session.commit()
            session.refresh(task)
            return [TextContent(type="text", text=json.dumps({
                "ok": True,
                "task": {
                    "id": task.id,
                    "title": task.title,
                    "category": task.category,
                    "difficulty": task.difficulty,
                    "xp": task.xp,
                    "active": task.active,
                    "completed": task.completed,
                }
            }))]

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
