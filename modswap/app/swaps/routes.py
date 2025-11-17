from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from ..extensions import db
from ..models import Module, SwapRequest


swaps_bp = Blueprint("swaps", __name__, template_folder="templates")


@swaps_bp.get("/")
@login_required
def browse():
    q = db.session.execute(db.select(SwapRequest).order_by(SwapRequest.created_at.desc())).scalars().all()
    return render_template("swaps/browse.html", swaps=q)


@swaps_bp.get("/create")
@login_required
def create():
    modules = db.session.execute(db.select(Module).order_by(Module.code)).scalars().all()
    return render_template("swaps/create.html", modules=modules)


@swaps_bp.post("/create")
@login_required
def create_post():
    give_ids = request.form.getlist("give")
    want_ids = request.form.getlist("want")
    swap = SwapRequest(user_id=current_user.id)
    for mid in give_ids:
        m = db.session.get(Module, int(mid))
        if m:
            swap.giving.append(m)
    for mid in want_ids:
        m = db.session.get(Module, int(mid))
        if m:
            swap.wanting.append(m)
    db.session.add(swap)
    db.session.commit()
    return redirect(url_for("swaps.browse"))