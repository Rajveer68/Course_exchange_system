from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from ..extensions import db
from ..models import Module, SwapRequest


swaps_bp = Blueprint("swaps", __name__, template_folder="templates")


@swaps_bp.get("/")
@login_required
def browse():
    if session.get("role") == "teacher":
        return redirect(url_for("admin.swaps"))
    swaps = db.session.execute(
        db.select(SwapRequest)
        .filter_by(user_id=current_user.id)
        .order_by(SwapRequest.created_at.desc())
    ).scalars().all()
    query = request.args.get("q", "").strip().lower()
    if query:
        def match_swap(s):
            items = list(s.giving) + list(s.wanting)
            for m in items:
                if query in (m.code or "").lower() or query in (m.name or "").lower() or query in (m.department or "").lower():
                    return True
            return False
        swaps = [s for s in swaps if match_swap(s)]
    return render_template("swaps/browse.html", swaps=swaps, q=request.args.get("q", ""))


@swaps_bp.get("/create")
@login_required
def create():
    if session.get("role") == "teacher":
        return redirect(url_for("admin.swaps"))
    modules = db.session.execute(db.select(Module).order_by(Module.department, Module.year, Module.code)).scalars().all()
    return render_template("swaps/create.html", modules=modules)


@swaps_bp.post("/create")
@login_required
def create_post():
    if session.get("role") == "teacher":
        return redirect(url_for("admin.swaps"))
    give_ids = request.form.getlist("give")
    want_ids = request.form.getlist("want")
    notes = request.form.get("notes")
    priority = request.form.get("priority")
    expires_on = request.form.get("expires_on")
    timeslots = request.form.get("timeslots")
    campus = request.form.get("campus")
    module_group_pref = request.form.get("module_group_pref")
    visibility = request.form.get("visibility", "public")
    alerts_email = request.form.get("alerts_email") == "on"
    auto_create_chat = request.form.get("auto_create_chat") == "on"

    if not give_ids or not want_ids:
        flash("Select at least one module to give and one to want")
        return redirect(url_for("swaps.create"))
    if len(give_ids) > 5 or len(want_ids) > 5:
        flash("You can select up to 5 modules in each list")
        return redirect(url_for("swaps.create"))
    if set(give_ids) & set(want_ids):
        flash("You cannot give and want the same module")
        return redirect(url_for("swaps.create"))
    existing_open = db.session.execute(
        db.select(SwapRequest).filter_by(user_id=current_user.id, status="Open")
    ).scalars().all()
    gi_set = {int(x) for x in give_ids}
    wi_set = {int(x) for x in want_ids}
    for s in existing_open:
        s_g = {m.id for m in s.giving}
        s_w = {m.id for m in s.wanting}
        if s_g == gi_set and s_w == wi_set:
            flash("Duplicate request already exists")
            return redirect(url_for("swaps.create"))

    swap = SwapRequest(user_id=current_user.id,
                       notes=notes,
                       priority=priority,
                       timeslots=timeslots,
                       campus=campus,
                       module_group_pref=module_group_pref,
                       visibility=visibility,
                       alerts_email=alerts_email,
                       auto_create_chat=auto_create_chat)
    if expires_on:
        try:
            from datetime import datetime
            swap.expires_at = datetime.strptime(expires_on.strip(), "%Y-%m-%d")
        except Exception:
            flash("Invalid expiry date format, use YYYY-MM-DD")
            return redirect(url_for("swaps.create"))
    for mid in give_ids:
        if m := db.session.get(Module, int(mid)):
            swap.giving.append(m)
    for mid in want_ids:
        if m := db.session.get(Module, int(mid)):
            swap.wanting.append(m)
    db.session.add(swap)
    db.session.commit()
    return redirect(url_for("swaps.browse"))

@swaps_bp.post("/suggest")
@login_required
def suggest():
    give_ids = {int(x) for x in request.form.getlist("give")}
    want_ids = {int(x) for x in request.form.getlist("want")}
    others = db.session.execute(
        db.select(SwapRequest).filter(SwapRequest.user_id != current_user.id)
    ).scalars().all()
    suggestions = []
    for s in others:
        s_g = {m.id for m in s.giving}
        s_w = {m.id for m in s.wanting}
        score = 0
        if s_w & give_ids:
            score += len(s_w & give_ids)
        if s_g & want_ids:
            score += len(s_g & want_ids)
        if score > 0:
            suggestions.append({"swap": s, "score": score})
    suggestions.sort(key=lambda x: x["score"], reverse=True)
    return render_template("swaps/_suggestions.html", suggestions=suggestions)
