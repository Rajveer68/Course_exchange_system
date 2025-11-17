import os
from flask import Flask
from .extensions import db, login_manager, bcrypt, mail, socketio
from .models import User
from .main.routes import main_bp
from .auth.routes import auth_bp
from .swaps.routes import swaps_bp
from .chat.routes import chat_bp


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
    return app