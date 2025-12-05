import os
from flask import Flask
 
from .extensions import db, login_manager, bcrypt, mail, socketio
from .models import User
from .main.routes import main_bp
from .profile.routes import profile_bp
from .auth.routes import auth_bp
from .swaps.routes import swaps_bp
from .chat.routes import chat_bp
from .admin.routes import admin_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object("modswap.config.Config")
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    bcrypt.init_app(app)
    mail.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    

    app.register_blueprint(main_bp)
    app.register_blueprint(profile_bp, url_prefix="/profile")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(swaps_bp, url_prefix="/swaps")
    app.register_blueprint(chat_bp, url_prefix="/chat")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    with app.app_context():
        from sqlalchemy import inspect, text
        insp = inspect(db.engine)
        if "users" in insp.get_table_names():
            cols = {c["name"] for c in insp.get_columns("users")}
            changed = False
            if "username" not in cols:
                db.session.execute(text("ALTER TABLE users ADD COLUMN username VARCHAR(255)"))
                changed = True
            if "role" not in cols:
                db.session.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(50)"))
                changed = True
            if "password_hash" not in cols:
                db.session.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)"))
                changed = True
            if "profile_image" not in cols:
                db.session.execute(text("ALTER TABLE users ADD COLUMN profile_image VARCHAR(255)"))
                changed = True
            if "department" not in cols:
                db.session.execute(text("ALTER TABLE users ADD COLUMN department VARCHAR(255)"))
                changed = True
            if "bio" not in cols:
                db.session.execute(text("ALTER TABLE users ADD COLUMN bio TEXT"))
                changed = True
            if "interests" not in cols:
                db.session.execute(text("ALTER TABLE users ADD COLUMN interests TEXT"))
                changed = True
            if "email_notifications" not in cols:
                db.session.execute(text("ALTER TABLE users ADD COLUMN email_notifications BOOLEAN DEFAULT 0"))
                changed = True
            if "verified_ac_email" not in cols:
                db.session.execute(text("ALTER TABLE users ADD COLUMN verified_ac_email BOOLEAN DEFAULT 0"))
                changed = True
            if "student_id_status" not in cols:
                db.session.execute(text("ALTER TABLE users ADD COLUMN student_id_status VARCHAR(50) DEFAULT 'None'"))
                changed = True
            if "preferred_timeslots" not in cols:
                db.session.execute(text("ALTER TABLE users ADD COLUMN preferred_timeslots VARCHAR(255)"))
                changed = True
            if "campus" not in cols:
                db.session.execute(text("ALTER TABLE users ADD COLUMN campus VARCHAR(255)"))
                changed = True
            if "preferred_module_groups" not in cols:
                db.session.execute(text("ALTER TABLE users ADD COLUMN preferred_module_groups TEXT"))
                changed = True
            if "show_university" not in cols:
                db.session.execute(text("ALTER TABLE users ADD COLUMN show_university BOOLEAN DEFAULT 1"))
                changed = True
            if "show_modules" not in cols:
                db.session.execute(text("ALTER TABLE users ADD COLUMN show_modules BOOLEAN DEFAULT 1"))
                changed = True
            if "show_bio" not in cols:
                db.session.execute(text("ALTER TABLE users ADD COLUMN show_bio BOOLEAN DEFAULT 1"))
                changed = True
            if "consent_data_usage" not in cols:
                db.session.execute(text("ALTER TABLE users ADD COLUMN consent_data_usage BOOLEAN DEFAULT 0"))
                changed = True
            if changed:
                db.session.commit()
        if "swap_requests" in insp.get_table_names():
            cols = {c["name"] for c in insp.get_columns("swap_requests")}
            changed = False
            if "notes" not in cols:
                db.session.execute(text("ALTER TABLE swap_requests ADD COLUMN notes TEXT"))
                changed = True
            if "priority" not in cols:
                db.session.execute(text("ALTER TABLE swap_requests ADD COLUMN priority VARCHAR(20)"))
                changed = True
            if "expires_at" not in cols:
                db.session.execute(text("ALTER TABLE swap_requests ADD COLUMN expires_at DATETIME"))
                changed = True
            if "timeslots" not in cols:
                db.session.execute(text("ALTER TABLE swap_requests ADD COLUMN timeslots VARCHAR(255)"))
                changed = True
            if "campus" not in cols:
                db.session.execute(text("ALTER TABLE swap_requests ADD COLUMN campus VARCHAR(255)"))
                changed = True
            if "module_group_pref" not in cols:
                db.session.execute(text("ALTER TABLE swap_requests ADD COLUMN module_group_pref TEXT"))
                changed = True
            if "visibility" not in cols:
                db.session.execute(text("ALTER TABLE swap_requests ADD COLUMN visibility VARCHAR(20) DEFAULT 'public'"))
                changed = True
            if "alerts_email" not in cols:
                db.session.execute(text("ALTER TABLE swap_requests ADD COLUMN alerts_email BOOLEAN DEFAULT 0"))
                changed = True
            if "auto_create_chat" not in cols:
                db.session.execute(text("ALTER TABLE swap_requests ADD COLUMN auto_create_chat BOOLEAN DEFAULT 0"))
                changed = True
            if changed:
                db.session.commit()
        existing_tables = insp.get_table_names()
        if "documents" not in existing_tables:
            db.metadata.tables.get("documents")
            db.metadata.create_all(bind=db.engine, tables=[db.metadata.tables["documents"]])
        if "ratings" not in existing_tables:
            db.metadata.tables.get("ratings")
            db.metadata.create_all(bind=db.engine, tables=[db.metadata.tables["ratings"]])
        if "user_wishlist" not in existing_tables:
            db.metadata.tables.get("user_wishlist")
            db.metadata.create_all(bind=db.engine, tables=[db.metadata.tables["user_wishlist"]])
        admin_email = "vikramjeet.-3@mail.bcu.ac.uk"
        admin = db.session.execute(db.select(User).filter_by(email=admin_email)).scalar_one_or_none()
        if not admin:
            domain = admin_email.split("@")[1]
            uni = domain.replace(".ac.uk", "")
            pw = bcrypt.generate_password_hash("Vansh@123").decode("utf-8")
            admin = User(email=admin_email, university=uni, role="teacher", password_hash=pw)
            db.session.add(admin)
            db.session.commit()
        else:
            updated = False
            if getattr(admin, "role", "student") != "teacher":
                admin.role = "teacher"
                updated = True
            if not getattr(admin, "password_hash", None):
                admin.password_hash = bcrypt.generate_password_hash("Vansh@123").decode("utf-8")
                updated = True
            if updated:
                db.session.commit()
        students = [
            {"username": "vikramjeet", "email": "vikramjeet.-3@mail.bcu.ac.uk", "password": "Vansh@123"},
            {"username": "rajveer", "email": "rajveer.saini@mail.bcu.ac.uk", "password": "Raj@123"},
        ]
        for s in students:
            existing = db.session.execute(db.select(User).filter_by(email=s["email"]))
            existing = existing.scalar_one_or_none()
            if not existing:
                domain = s["email"].split("@")[1]
                uni = domain.replace(".ac.uk", "")
                pw = bcrypt.generate_password_hash(s["password"]).decode("utf-8")
                u = User(username=s["username"], email=s["email"], university=uni, role="student", password_hash=pw, verified_ac_email=True)
                db.session.add(u)
                db.session.commit()
            else:
                updated = False
                if getattr(existing, "username", None) != s["username"]:
                    existing.username = s["username"]
                    updated = True
                if getattr(existing, "role", "student") != "student":
                    existing.role = "student"
                    updated = True
                if not getattr(existing, "password_hash", None):
                    existing.password_hash = bcrypt.generate_password_hash(s["password"]).decode("utf-8")
                    updated = True
                if not getattr(existing, "verified_ac_email", False):
                    existing.verified_ac_email = True
                    updated = True
                if updated:
                    db.session.commit()
        return app
