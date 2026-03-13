from flask import Blueprint
from flask import session, redirect, render_template, request, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import get_accounts
from app.routes.auth import check_user

profile_bp = Blueprint('profile', __name__)


@profile_bp.route("/profile", methods=["GET", "POST"])
def profile():
    if not check_user(1):
        return redirect(url_for("auth.login"))

    conn = get_accounts()
    user = conn.execute(
        "SELECT id, uname, password FROM accounts WHERE id = ?", (session["user_id"],)).fetchone()

    error = None
    success = None

    if request.method == "POST":
        old_password = request.form["old_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if not check_password_hash(user["password"], old_password):
            error = "Altes Passwort ist falsch."
        elif new_password != confirm_password:
            error = "Die neuen Passwörter stimmen nicht überein."
        else:
            hashed = generate_password_hash(new_password)
            conn.execute(
                "UPDATE accounts SET password = ? WHERE id = ?", (hashed, user["id"]))
            conn.commit()
            success = "Passwort erfolgreich geändert."

    conn.close()
    return render_template("profile.html", user=user, error=error, success=success)