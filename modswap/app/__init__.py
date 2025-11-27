import os
from flask import Flask
from .extensions import db, login_manager, bcrypt, mail, socketio
from .models import User
from .main.routes import main_bp
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
            if "role" not in cols:
                db.session.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(50)"))
                changed = True
            if "password_hash" not in cols:
                db.session.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)"))
                changed = True
            if changed:
                db.session.commit()
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
    return app