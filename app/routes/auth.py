from functools import wraps

from flask import Blueprint, abort, redirect, render_template, request, session, url_for
from flask_login import current_user, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from app.models import User, get_accounts

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username", "").strip().lower()
    password = request.form.get("password", "")
    error = None

    with get_accounts() as conn:
        row = conn.execute(
            "SELECT id, password, role, status FROM accounts WHERE uname = ?",
            (username,),
        ).fetchone()

    if not row:
        error = "Falsche Kombination aus Benutzernamen und Passwort."
    elif row["status"] != "active":
        error = "Dein Konto wartet noch auf eine Adminbestätigung"
    elif not check_password_hash(row["password"], password):
        error = "Falsche Kombination aus Benutzernamen und Passwort."

    if error:
        return render_template("login.html", error=error)

    user = User(row["id"], username, row["role"])
    login_user(user)

    return redirect("/")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    session.clear()
    if request.method == "GET":
        return render_template("register.html")

    username = request.form.get("username", "").strip().lower()
    password = request.form.get("password", "")

    if not username or not password:
        return render_template(
            "register.html", error="Bitte Benutzername und Passwort eingeben."
        )

    hashed_password = generate_password_hash(password)

    with get_accounts() as conn:
        existing = conn.execute(
            "SELECT id FROM accounts WHERE uname = ?", (username,)
        ).fetchone()

        if existing:
            return render_template(
                "register.html", error="Benutzername existiert bereits."
            )

        conn.execute(
            "INSERT INTO accounts (uname, password, role, status) VALUES (?, ?, ?, ?)",
            (username, hashed_password, 1, "pending"),
        )

    return redirect("/")


@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


def require_role(level):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role < level:
                abort(403)
            return f(*args, **kwargs)

        return wrapper

    return decorator
