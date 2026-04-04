from flask import Blueprint, render_template, request
from flask_login import current_user, login_required
from werkzeug.security import check_password_hash

from app.routes.auth import require_role
from app.services.profile_service import *

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/profile", methods=["GET", "POST"])
@login_required
@require_role(1)
def profile():
    user = get_account(current_user)
    error = success = None

    if request.method == "POST":

        old_password = request.form.get("old_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not check_password_hash(user["password"], old_password):
            error = "Altes Passwort ist falsch."
        elif new_password != confirm_password:
            error = "Die neuen Passwörter stimmen nicht überein."
        else:
            update_password(user["id"], new_password)
            success = "Passwort erfolgreich geändert."

    return render_template("profile.html", user=user, error=error, success=success)
