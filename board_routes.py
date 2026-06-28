import calendar as cal
from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash, g, abort
from access_helpers import name_required, can_edit, get_reunion_by_id

board_bp = Blueprint("board", __name__, url_prefix="/r/<reunion_id>")


def _get_reunion_or_404(reunion_id):
    reunion = get_reunion_by_id(reunion_id)
    if not reunion:
        abort(404)
    return reunion


def _require_edit(reunion_id):
    if not can_edit(reunion_id):
        flash("Enter the edit code to make changes.", "warning")
        return False
    return True


def _comment_counts(reunion_id):
    res = g.sb.table("comments").select("parent_type, parent_id").eq("reunion_id", reunion_id).execute()
    counts = {}
    for row in res.data or []:
        key = (row["parent_type"], row["parent_id"])
        counts[key] = counts.get(key, 0) + 1
    return counts


@board_bp.route("/")
@name_required
def overview(reunion_id):
    reunion = _get_reunion_or_404(reunion_id)
    editing = can_edit(reunion_id)

    tasks = g.sb.table("tasks").select("*").eq("reunion_id", reunion_id).execute().data or []
    events = g.sb.table("events").select("*").eq("reunion_id", reunion_id).execute().data or []
    people = g.sb.table("people").select("*").eq("reunion_id", reunion_id).execute().data or []
    places = g.sb.table("places").select("*").eq("reunion_id", reunion_id).execute().data or []

    open_tasks = [t for t in tasks if not t["claimed_by_name"]]
    my_tasks = [t for t in tasks if t["claimed_by_name"] == g.name]
    going = [p for p in people if p["rsvp"] == "yes"]
    upcoming = sorted(events, key=lambda e: e.get("event_date") or "9999-99-99")[:3]

    return render_template(
        "overview.html",
        reunion=reunion,
        reunion_id=reunion_id,
        editing=editing,
        open_tasks=open_tasks,
        my_tasks=my_tasks,
        upcoming=upcoming,
        task_count=len(tasks),
        event_count=len(events),
        going_count=len(going),
        people_count=len(people),
        places_count=len(places),
    )


# ---------------- Tasks ----------------

@board_bp.route("/tasks")
@name_required
def tasks(reunion_id):
    reunion = _get_reunion_or_404(reunion_id)
    editing = can_edit(reunion_id)
    all_tasks = g.sb.table("tasks").select("*").eq("reunion_id", reunion_id).order("created_at", desc=True).execute().data or []
    counts = _comment_counts(reunion_id)
    for t in all_tasks:
        t["comment_count"] = counts.get(("task", t["id"]), 0)
    return render_template("tasks.html", reunion=reunion, reunion_id=reunion_id, tasks=all_tasks, editing=editing)


@board_bp.route("/tasks/create", methods=["POST"])
@name_required
def create_task(reunion_id):
    _get_reunion_or_404(reunion_id)
    if not _require_edit(reunion_id):
        return redirect(url_for("board.tasks", reunion_id=reunion_id))
    g.sb.table("tasks").insert({
        "reunion_id": reunion_id,
        "title": request.form.get("title", "").strip(),
        "category": request.form.get("category", "general"),
        "notes": request.form.get("notes", "").strip(),
        "created_by_name": g.name,
    }).execute()
    return redirect(url_for("board.tasks", reunion_id=reunion_id))


@board_bp.route("/tasks/<task_id>/claim", methods=["POST"])
@name_required
def claim_task(reunion_id, task_id):
    _get_reunion_or_404(reunion_id)
    if not _require_edit(reunion_id):
        return redirect(url_for("board.tasks", reunion_id=reunion_id))
    g.sb.table("tasks").update({"claimed_by_name": g.name}).eq("id", task_id).execute()
    return redirect(url_for("board.tasks", reunion_id=reunion_id))


@board_bp.route("/tasks/<task_id>/release", methods=["POST"])
@name_required
def release_task(reunion_id, task_id):
    _get_reunion_or_404(reunion_id)
    if not _require_edit(reunion_id):
        return redirect(url_for("board.tasks", reunion_id=reunion_id))
    g.sb.table("tasks").update({"claimed_by_name": None, "done": False}).eq("id", task_id).execute()
    return redirect(url_for("board.tasks", reunion_id=reunion_id))


@board_bp.route("/tasks/<task_id>/toggle-done", methods=["POST"])
@name_required
def toggle_task_done(reunion_id, task_id):
    _get_reunion_or_404(reunion_id)
    if not _require_edit(reunion_id):
        return redirect(url_for("board.tasks", reunion_id=reunion_id))
    current = g.sb.table("tasks").select("done").eq("id", task_id).execute().data
    if current:
        g.sb.table("tasks").update({"done": not current[0]["done"]}).eq("id", task_id).execute()
    return redirect(url_for("board.tasks", reunion_id=reunion_id))


@board_bp.route("/tasks/<task_id>/delete", methods=["POST"])
@name_required
def delete_task(reunion_id, task_id):
    _get_reunion_or_404(reunion_id)
    if not _require_edit(reunion_id):
        return redirect(url_for("board.tasks", reunion_id=reunion_id))
    g.sb.table("tasks").delete().eq("id", task_id).execute()
    return redirect(url_for("board.tasks", reunion_id=reunion_id))


# ---------------- Events + Calendar ----------------

@board_bp.route("/events")
@name_required
def events(reunion_id):
    reunion = _get_reunion_or_404(reunion_id)
    editing = can_edit(reunion_id)
    all_events = g.sb.table("events").select("*").eq("reunion_id", reunion_id).order("event_date").execute().data or []
    counts = _comment_counts(reunion_id)
    for e in all_events:
        e["comment_count"] = counts.get(("event", e["id"]), 0)
    return render_template("events.html", reunion=reunion, reunion_id=reunion_id, events=all_events, editing=editing)


@board_bp.route("/events/create", methods=["POST"])
@name_required
def create_event(reunion_id):
    _get_reunion_or_404(reunion_id)
    if not _require_edit(reunion_id):
        return redirect(url_for("board.events", reunion_id=reunion_id))
    g.sb.table("events").insert({
        "reunion_id": reunion_id,
        "title": request.form.get("title", "").strip(),
        "event_date": request.form.get("event_date") or None,
        "event_time": request.form.get("event_time") or None,
        "location": request.form.get("location", "").strip(),
        "details": request.form.get("details", "").strip(),
        "created_by_name": g.name,
    }).execute()
    return redirect(url_for("board.events", reunion_id=reunion_id))


@board_bp.route("/events/<event_id>/delete", methods=["POST"])
@name_required
def delete_event(reunion_id, event_id):
    _get_reunion_or_404(reunion_id)
    if not _require_edit(reunion_id):
        return redirect(url_for("board.events", reunion_id=reunion_id))
    g.sb.table("events").delete().eq("id", event_id).execute()
    return redirect(url_for("board.events", reunion_id=reunion_id))


@board_bp.route("/calendar")
@board_bp.route("/calendar/<int:year>/<int:month>")
@name_required
def calendar_view(reunion_id, year=None, month=None):
    reunion = _get_reunion_or_404(reunion_id)
    today = date.today()
    year = year or today.year
    month = month or today.month

    all_events = g.sb.table("events").select("*").eq("reunion_id", reunion_id).execute().data or []

    events_by_day = {}
    for e in all_events:
        if not e.get("event_date"):
            continue
        d = date.fromisoformat(e["event_date"])
        if d.year == year and d.month == month:
            events_by_day.setdefault(d.day, []).append(e)

    for day_events in events_by_day.values():
        day_events.sort(key=lambda e: e.get("event_time") or "99:99")

    cal.setfirstweekday(cal.SUNDAY)
    month_grid = cal.monthcalendar(year, month)

    prev_month = month - 1 or 12
    prev_year = year - 1 if month == 1 else year
    next_month = month + 1 if month < 12 else 1
    next_year = year + 1 if month == 12 else year

    return render_template(
        "calendar.html",
        reunion=reunion,
        reunion_id=reunion_id,
        year=year,
        month=month,
        month_name=cal.month_name[month],
        month_grid=month_grid,
        events_by_day=events_by_day,
        today=today,
        prev_year=prev_year,
        prev_month=prev_month,
        next_year=next_year,
        next_month=next_month,
    )


# ---------------- Notes ----------------

@board_bp.route("/notes")
@name_required
def notes(reunion_id):
    reunion = _get_reunion_or_404(reunion_id)
    editing = can_edit(reunion_id)
    all_notes = g.sb.table("notes").select("*").eq("reunion_id", reunion_id).order("created_at", desc=True).execute().data or []
    counts = _comment_counts(reunion_id)
    for n in all_notes:
        n["comment_count"] = counts.get(("note", n["id"]), 0)
    return render_template("notes.html", reunion=reunion, reunion_id=reunion_id, notes=all_notes, editing=editing)


@board_bp.route("/notes/create", methods=["POST"])
@name_required
def create_note(reunion_id):
    _get_reunion_or_404(reunion_id)
    if not _require_edit(reunion_id):
        return redirect(url_for("board.notes", reunion_id=reunion_id))
    text = request.form.get("text", "").strip()
    if text:
        g.sb.table("notes").insert({
            "reunion_id": reunion_id, "text": text, "author_name": g.name
        }).execute()
    return redirect(url_for("board.notes", reunion_id=reunion_id))


@board_bp.route("/notes/<note_id>/delete", methods=["POST"])
@name_required
def delete_note(reunion_id, note_id):
    _get_reunion_or_404(reunion_id)
    if not _require_edit(reunion_id):
        return redirect(url_for("board.notes", reunion_id=reunion_id))
    g.sb.table("notes").delete().eq("id", note_id).execute()
    return redirect(url_for("board.notes", reunion_id=reunion_id))


# ---------------- People / RSVP ----------------

@board_bp.route("/people")
@name_required
def people(reunion_id):
    reunion = _get_reunion_or_404(reunion_id)
    editing = can_edit(reunion_id)
    all_people = g.sb.table("people").select("*").eq("reunion_id", reunion_id).order("created_at").execute().data or []
    my_entry = next((p for p in all_people if p["name"] == g.name), None)
    return render_template(
        "people.html", reunion=reunion, reunion_id=reunion_id, people=all_people,
        editing=editing, my_entry=my_entry
    )


@board_bp.route("/people/rsvp", methods=["POST"])
@name_required
def set_rsvp(reunion_id):
    _get_reunion_or_404(reunion_id)
    rsvp = request.form.get("rsvp", "unknown")

    existing = g.sb.table("people").select("id").eq("reunion_id", reunion_id).eq("name", g.name).execute().data
    if existing:
        g.sb.table("people").update({"rsvp": rsvp}).eq("id", existing[0]["id"]).execute()
    else:
        g.sb.table("people").insert({"reunion_id": reunion_id, "name": g.name, "rsvp": rsvp}).execute()

    return redirect(url_for("board.people", reunion_id=reunion_id))


# ---------------- Places (lodging / venue details) ----------------

@board_bp.route("/places")
@name_required
def places(reunion_id):
    reunion = _get_reunion_or_404(reunion_id)
    editing = can_edit(reunion_id)
    all_places = g.sb.table("places").select("*").eq("reunion_id", reunion_id).order("created_at").execute().data or []
    return render_template("places.html", reunion=reunion, reunion_id=reunion_id, places=all_places, editing=editing)


@board_bp.route("/places/create", methods=["POST"])
@name_required
def create_place(reunion_id):
    _get_reunion_or_404(reunion_id)
    if not _require_edit(reunion_id):
        return redirect(url_for("board.places", reunion_id=reunion_id))
    g.sb.table("places").insert({
        "reunion_id": reunion_id,
        "name": request.form.get("name", "").strip(),
        "address": request.form.get("address", "").strip(),
        "check_in": request.form.get("check_in") or None,
        "check_out": request.form.get("check_out") or None,
        "wifi_network": request.form.get("wifi_network", "").strip(),
        "wifi_password": request.form.get("wifi_password", "").strip(),
        "host_name": request.form.get("host_name", "").strip(),
        "host_contact": request.form.get("host_contact", "").strip(),
        "notes": request.form.get("notes", "").strip(),
        "created_by_name": g.name,
    }).execute()
    return redirect(url_for("board.places", reunion_id=reunion_id))


@board_bp.route("/places/<place_id>/delete", methods=["POST"])
@name_required
def delete_place(reunion_id, place_id):
    _get_reunion_or_404(reunion_id)
    if not _require_edit(reunion_id):
        return redirect(url_for("board.places", reunion_id=reunion_id))
    g.sb.table("places").delete().eq("id", place_id).execute()
    return redirect(url_for("board.places", reunion_id=reunion_id))


# ---------------- Comments ----------------

@board_bp.route("/comments/<parent_type>/<parent_id>/add", methods=["POST"])
@name_required
def add_comment(reunion_id, parent_type, parent_id):
    _get_reunion_or_404(reunion_id)
    if parent_type not in ("task", "event", "note"):
        abort(400)
    redirect_map = {"task": "board.tasks", "event": "board.events", "note": "board.notes"}
    if not _require_edit(reunion_id):
        return redirect(url_for(redirect_map[parent_type], reunion_id=reunion_id))

    body = request.form.get("body", "").strip()
    if body:
        g.sb.table("comments").insert({
            "reunion_id": reunion_id,
            "parent_type": parent_type,
            "parent_id": parent_id,
            "body": body,
            "author_name": g.name,
        }).execute()

    return redirect(url_for(redirect_map[parent_type], reunion_id=reunion_id) + f"#comments-{parent_id}")


@board_bp.route("/comments/<parent_type>/<parent_id>")
@name_required
def view_comments(reunion_id, parent_type, parent_id):
    _get_reunion_or_404(reunion_id)
    comments = (
        g.sb.table("comments")
        .select("*")
        .eq("reunion_id", reunion_id)
        .eq("parent_type", parent_type)
        .eq("parent_id", parent_id)
        .order("created_at")
        .execute()
        .data
        or []
    )
    editing = can_edit(reunion_id)
    return render_template(
        "_comments.html",
        comments=comments,
        reunion_id=reunion_id,
        parent_type=parent_type,
        parent_id=parent_id,
        editing=editing,
    )
