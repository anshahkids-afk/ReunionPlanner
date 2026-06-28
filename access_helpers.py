"""
Access helpers for the code-based version of the app.

There are no user accounts. Instead:
- Each reunion has a `plan_code` (lets you VIEW the board) and an
  `edit_code` (lets you also CHANGE things).
- A person types their name once per browser session, then enters a
  plan code to get in, and can unlock editing later by entering the
  edit code.
- Flask's session (a signed cookie) just remembers: your name, which
  reunion you're looking at, and whether you've unlocked editing for it.
"""
import random
import string
from functools import wraps
from flask import session, redirect, url_for, flash, g
from config import get_supabase_client


def generate_code(length=6):
    """Short, easy-to-read code: uppercase letters + digits, no 0/O/1/I mixups."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(random.choice(alphabet) for _ in range(length))


def get_reunion_by_plan_code(plan_code: str):
    sb = get_supabase_client()
    res = sb.table("reunions").select("*").eq("plan_code", plan_code.strip().upper()).execute()
    return res.data[0] if res.data else None


def get_reunion_by_id(reunion_id: str):
    sb = get_supabase_client()
    res = sb.table("reunions").select("*").eq("id", reunion_id).execute()
    return res.data[0] if res.data else None


def current_name():
    return session.get("name")


def can_edit(reunion_id: str) -> bool:
    return session.get("edit_unlocked_for") == reunion_id


def name_required(view_func):
    """Make sure the person has typed a name before doing anything."""
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("name"):
            flash("Let us know your name first.", "warning")
            return redirect(url_for("access.home"))
        g.sb = get_supabase_client()
        g.name = session["name"]
        return view_func(*args, **kwargs)
    return wrapped
