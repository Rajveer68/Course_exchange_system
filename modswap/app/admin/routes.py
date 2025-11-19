from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required
from ..extensions import db
from ..models import SwapRequest


admin_bp = Blueprint("admin", __name__, template_folder="templates")


def teacher_only():
    from flask import session
    return session.get("role") == "teacher"


@admin_bp.get("/swaps")
@login_required
def swaps():
    if not teacher_only():
        return redirect(url_for("auth.login"))
    q = db.session.execute(db.select(SwapRequest).order_by(SwapRequest.created_at.desc())).scalars().all()
    return render_template("admin/swaps.html", swaps=q)


@admin_bp.post("/swaps/<int:swap_id>/status")
@login_required
def set_status(swap_id: int):
    if not teacher_only():
        return redirect(url_for("auth.login"))
    status = request.form.get("status")
    s = db.session.get(SwapRequest, swap_id)
    if s and status in {"Approved", "Rejected"}:
        s.status = status
        db.session.commit()
    return redirect(url_for("admin.swaps"))