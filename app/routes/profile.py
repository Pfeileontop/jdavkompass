from flask import Blueprint, render_template, request
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import get_accounts
from flask_login import login_required, current_user
from app.routes.auth import require_role

profile_bp = Blueprint('profile', __name__)

@profile_bp.route("/profile", methods=["GET", "POST"])
@login_required
@require_role(1)
def profile():
    error = None
    success = None

    with get_accounts() as conn:
        # Load user data from DB
        user = conn.execute(
            "SELECT id, uname, password FROM accounts WHERE id = ?",
            (current_user.id,)
        ).fetchone()

        if request.method == "POST":
            old_password = request.form.get("old_password", "")
            new_password = request.form.get("new_password", "")
            confirm_password = request.form.get("confirm_password", "")

            if not check_password_hash(user["password"], old_password):
                error = "Altes Passwort ist falsch."
            elif new_password != confirm_password:
                error = "Die neuen Passwörter stimmen nicht überein."
            else:
                hashed = generate_password_hash(new_password)
                conn.execute(
                    "UPDATE accounts SET password = ? WHERE id = ?", 
                    (hashed, user["id"])
                )
                conn.commit()
                success = "Passwort erfolgreich geändert."

    return render_template("profile.html", user=user, error=error, success=success)