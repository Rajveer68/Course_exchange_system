from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required
from ..extensions import db
from ..models import SwapRequest, Module


admin_bp = Blueprint("admin", __name__, template_folder="templates")


def teacher_only():
    from flask import session
    return session.get("role") == "teacher"


@admin_bp.get("/swaps")
@login_required
def swaps():
    if not teacher_only():
        return redirect(url_for("auth.login"))
    status = request.args.get("status")
    dept = (request.args.get("department") or "").strip().lower()
    year = request.args.get("year")
    priority = request.args.get("priority")
    search = (request.args.get("q") or "").strip().lower()
    expires_before = request.args.get("expires_before")
    base = db.select(SwapRequest)
    if status:
        base = base.filter_by(status=status)
    if priority:
        base = base.filter_by(priority=priority)
    swaps = db.session.execute(base.order_by(SwapRequest.created_at.desc())).scalars().all()
    def matches_filters(s: SwapRequest) -> bool:
        modules = list(s.giving) + list(s.wanting)
        ok_dept = True
        ok_year = True
        if dept:
            ok_dept = any((m.department or "").lower() == dept for m in modules)
        if year:
            try:
                yr = int(year)
                ok_year = any((m.year or 0) == yr for m in modules)
            except Exception:
                ok_year = True
        ok_search = True
        if search:
            ok_search = any(search in (m.code or '').lower() or search in (m.name or '').lower() or search in (m.department or '').lower() for m in modules) or (search in (s.notes or '').lower())
        ok_expiry = True
        if expires_before and s.expires_at:
            try:
                from datetime import datetime
                import datetime as dt
                cutoff = datetime.strptime(expires_before, "%Y-%m-%d")
                ok_expiry = s.expires_at <= cutoff
            except Exception:
                ok_expiry = True
        return ok_dept and ok_year and ok_search and ok_expiry
    swaps = [s for s in swaps if matches_filters(s)]
    others = swaps
    def score_for(s: SwapRequest) -> int:
        s_g = {m.id for m in s.giving}
        s_w = {m.id for m in s.wanting}
        score = 0
        for o in others:
            if o.id == s.id:
                continue
            o_g = {m.id for m in o.giving}
            o_w = {m.id for m in o.wanting}
            score += len(o_w & s_g) + len(o_g & s_w)
        return score
    annotated = []
    from datetime import datetime
    for s in swaps:
        days_left = None
        if s.expires_at:
            days_left = (s.expires_at - datetime.utcnow()).days
        annotated.append({"swap": s, "score": score_for(s), "days_left": days_left})
    return render_template("admin/swaps.html", swaps=annotated)


@admin_bp.post("/swaps/<int:swap_id>/status")
@login_required
def set_status(swap_id: int):
    if not teacher_only():
        return redirect(url_for("auth.login"))
    status = request.form.get("status")
    s = db.session.get(SwapRequest, swap_id)
    if s and status in {"Approved", "Rejected", "Needs Info"}:
        if status in {"Approved", "Rejected"}:
            db.session.delete(s)
            db.session.commit()
        else:
            s.status = status
            db.session.commit()
    return redirect(url_for("admin.swaps"))


@admin_bp.post("/swaps/bulk")
@login_required
def bulk():
    if not teacher_only():
        return redirect(url_for("auth.login"))
    action = request.form.get("action")
    ids = [int(x) for x in request.form.getlist("ids")]
    rows = db.session.execute(db.select(SwapRequest).filter(SwapRequest.id.in_(ids))).scalars().all()
    if action in {"approve", "reject", "needs_info"}:
        if action in {"approve", "reject"}:
            for r in rows:
                db.session.delete(r)
            db.session.commit()
        else:
            for r in rows:
                r.status = "Needs Info"
            db.session.commit()
        flash(f"Updated {len(rows)} request(s)")
    return redirect(url_for("admin.swaps"))
