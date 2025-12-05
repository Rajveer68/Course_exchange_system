import os
import json
from flask import Blueprint, render_template, request, redirect, url_for, current_app, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from ..extensions import db
from ..models import User, Module, SwapRequest, Document, Notification

profile_bp = Blueprint("profile", __name__, template_folder="templates")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@profile_bp.get("/")
@login_required
def view_profile():
    swaps = db.session.execute(
        db.select(SwapRequest).filter_by(user_id=current_user.id).order_by(SwapRequest.created_at.desc())
    ).scalars().all()
    stats = {
        "requests": len(swaps),
        "approved": sum(1 for s in swaps if s.status == "Approved"),
        "rejected": sum(1 for s in swaps if s.status == "Rejected"),
    }
    return render_template("profile/view.html", user=current_user, swaps=swaps, stats=stats)

@profile_bp.post("/")
@login_required
def update_profile():
    u = db.session.get(User, current_user.id)
    u.degree = request.form.get("degree") or u.degree
    u.year = int(request.form.get("year") or u.year or 0) or None
    u.department = request.form.get("department") or u.department
    u.bio = request.form.get("bio") or u.bio
    u.interests = request.form.get("interests") or u.interests
    u.preferred_timeslots = request.form.get("preferred_timeslots") or u.preferred_timeslots
    u.campus = request.form.get("campus") or u.campus
    u.preferred_module_groups = request.form.get("preferred_module_groups") or u.preferred_module_groups
    u.email_notifications = request.form.get("email_notifications") == "on"
    u.show_university = request.form.get("show_university") == "on"
    u.show_modules = request.form.get("show_modules") == "on"
    u.show_bio = request.form.get("show_bio") == "on"
    u.consent_data_usage = request.form.get("consent_data_usage") == "on"
    file = request.files.get("avatar")
    if file and file.filename != "":
        if not allowed_file(file.filename):
            flash("Invalid image type")
            return redirect(url_for("profile.view_profile"))
        uploads_dir = os.path.join(current_app.root_path, "static", "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        ext = file.filename.rsplit(".", 1)[1].lower()
        filename = f"user_{current_user.id}.{ext}"
        filepath = os.path.join(uploads_dir, secure_filename(filename))
        file.save(filepath)
        u.profile_image = f"uploads/{filename}"
    db.session.commit()
    flash("Profile updated")
    return redirect(url_for("profile.view_profile"))

@profile_bp.post("/avatar/delete")
@login_required
def delete_avatar():
    u = db.session.get(User, current_user.id)
    if u.profile_image:
        path = os.path.join(current_app.root_path, "static", u.profile_image)
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass
        u.profile_image = None
        db.session.commit()
    flash("Avatar deleted")
    return redirect(url_for("profile.view_profile"))

@profile_bp.post("/wishlist/add")
@login_required
def wishlist_add():
    mid = request.form.get("module_id")
    m = db.session.get(Module, int(mid)) if mid else None
    if m and m not in current_user.wishlist:
        current_user.wishlist.append(m)
        db.session.commit()
    return redirect(url_for("profile.view_profile"))

@profile_bp.post("/wishlist/remove")
@login_required
def wishlist_remove():
    mid = request.form.get("module_id")
    m = db.session.get(Module, int(mid)) if mid else None
    if m and m in current_user.wishlist:
        current_user.wishlist.remove(m)
        db.session.commit()
    return redirect(url_for("profile.view_profile"))

@profile_bp.post("/wishlist/create_request")
@login_required
def wishlist_create_request():
    swap = SwapRequest(user_id=current_user.id)
    for m in current_user.wishlist:
        swap.wanting.append(m)
    db.session.add(swap)
    db.session.commit()
    flash("Swap request created from wishlist")
    return redirect(url_for("profile.view_profile"))

@profile_bp.get("/export")
@login_required
def export_profile():
    data = {
        "email": current_user.email,
        "university": current_user.university,
        "degree": current_user.degree,
        "year": current_user.year,
        "department": current_user.department,
        "bio": current_user.bio,
        "interests": current_user.interests,
        "modules": [{"code": m.code, "name": m.name} for m in current_user.modules],
    }
    return jsonify(data)

@profile_bp.post("/documents/upload")
@login_required
def upload_document():
    dtype = request.form.get("type") or "student_id"
    file = request.files.get("document")
    if not file or file.filename == "":
        flash("Select a document to upload")
        return redirect(url_for("profile.view_profile"))
    uploads_dir = os.path.join(current_app.root_path, "static", "docs")
    os.makedirs(uploads_dir, exist_ok=True)
    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = f"doc_{current_user.id}_{dtype}.{ext}"
    filepath = os.path.join(uploads_dir, secure_filename(filename))
    file.save(filepath)
    doc = Document(user_id=current_user.id, type=dtype, path=f"docs/{filename}", status="Pending")
    db.session.add(doc)
    u = db.session.get(User, current_user.id)
    u.student_id_status = "Pending"
    db.session.commit()
    flash("Document uploaded")
    return redirect(url_for("profile.view_profile"))

@profile_bp.post("/reminders/add")
@login_required
def add_reminder():
    payload = {
        "type": "deadline",
        "department": request.form.get("deadline_department") or "",
        "date": request.form.get("deadline_date") or "",
        "note": request.form.get("deadline_note") or "",
    }
    n = Notification(user_id=current_user.id, type="deadline", payload=json.dumps(payload))
    db.session.add(n)
    db.session.commit()
    flash("Reminder added")
    return redirect(url_for("profile.view_profile"))
