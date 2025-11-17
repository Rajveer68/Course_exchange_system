import re
from urllib.parse import urlparse
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask import current_app
from ..extensions import db
from ..models import User


auth_bp = Blueprint("auth", __name__, template_folder="templates")


def serializer(secret_key):
    return URLSafeTimedSerializer(secret_key)


def email_is_uni(email):
    return re.search(r"@.+\.ac\.uk$", email) is not None


@auth_bp.get("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    return render_template("auth/login.html")


@auth_bp.post("/login")
def send_magic_link():
    email = request.form.get("email", "").strip().lower()
    if not email_is_uni(email):
        flash("Use your university email ending with .ac.uk")
        return redirect(url_for("auth.login"))
    s = serializer(current_app.config["SECRET_KEY"])
    token = s.dumps(email)
    flash("Magic link generated. Use the Verify link to continue.")
    return redirect(url_for("auth.verify", token=token))


@auth_bp.get("/verify")
def verify():
    token = request.args.get("token")
    s = serializer(current_app.config["SECRET_KEY"])
    try:
        email = s.loads(token, max_age=900)
    except SignatureExpired:
        flash("Link expired")
        return redirect(url_for("auth.login"))
    except BadSignature:
        flash("Invalid link")
        return redirect(url_for("auth.login"))
    user = db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()
    if not user:
        domain = email.split("@")[-1]
        uni = domain.replace(".ac.uk", "")
        user = User(email=email, university=uni)
        db.session.add(user)
        db.session.commit()
    login_user(user)
    return redirect(url_for("main.index"))


@auth_bp.post("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.index"))