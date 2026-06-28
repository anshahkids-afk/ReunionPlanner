from flask import Blueprint, render_template, request, redirect, url_for, session, flash, g
from access_helpers import (
    generate_code, get_reunion_by_plan_code, get_reunion_by_id, name_required
)
from config import get_supabase_client

access_bp = Blueprint("access", __name__)


@access_bp.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Please enter your name.", "error")
            return render_template("home.html")
        session["name"] = name
        return redirect(url_for("access.home"))

    return render_template("home.html")


@access_bp.route("/change-name", methods=["POST"])
def change_name():
    session.pop("name", None)
    return redirect(url_for("access.home"))


@access_bp.route("/reunions/create", methods=["POST"])
@name_required
def create_reunion():
    name = request.form.get("name", "").strip() or "Our reunion"
    tagline = request.form.get("tagline", "").strip()

    plan_code = generate_code(6)
    edit_code = generate_code(6)

    created = g.sb.table("reunions").insert({
        "name": name,
        "tagline": tagline,
        "plan_code": plan_code,
        "edit_code": edit_code,
    }).execute()

    if not created.data:
        flash("Could not create reunion. Please try again.", "error")
        return redirect(url_for("access.home"))

    reunion = created.data[0]
    session["edit_unlocked_for"] = reunion["id"]  # creator starts off able to edit

    flash(
        f'"{name}" created! Plan code: {plan_code} · Edit code: {edit_code} '
        f"— share the plan code with everyone, and the edit code only with people "
        f"you want to be able to make changes.",
        "success",
    )
    return redirect(url_for("board.overview", reunion_id=reunion["id"]))


@access_bp.route("/reunions/enter", methods=["POST"])
@name_required
def enter_reunion():
    plan_code = request.form.get("plan_code", "").strip()
    if not plan_code:
        flash("Enter a plan code to continue.", "error")
        return redirect(url_for("access.home"))

    reunion = get_reunion_by_plan_code(plan_code)
    if not reunion:
        flash("That plan code doesn't match any reunion. Double-check it.", "error")
        return redirect(url_for("access.home"))

    return redirect(url_for("board.overview", reunion_id=reunion["id"]))


@access_bp.route("/r/<reunion_id>/unlock-editing", methods=["POST"])
@name_required
def unlock_editing(reunion_id):
    reunion = get_reunion_by_id(reunion_id)
    if not reunion:
        flash("Reunion not found.", "error")
        return redirect(url_for("access.home"))

    edit_code = request.form.get("edit_code", "").strip().upper()
    if edit_code == reunion["edit_code"]:
        session["edit_unlocked_for"] = reunion_id
        flash("Editing unlocked for this reunion.", "success")
    else:
        flash("That edit code isn't right.", "error")

    return redirect(url_for("board.overview", reunion_id=reunion_id))
