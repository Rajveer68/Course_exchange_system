from flask import Blueprint, render_template
from flask_login import login_required

chat_bp = Blueprint("chat", __name__, template_folder="templates")


@chat_bp.get("/")
@login_required
def index():
    return render_template("chat/thread.html")