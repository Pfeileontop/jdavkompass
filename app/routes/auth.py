from flask import Blueprint
from flask import request, render_template, session, redirect, url_for, abort
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import get_accounts
import sqlite3
from flask_login import login_user, logout_user
from app.models import User
from functools import wraps
from flask_login import current_user
from flask import abort

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    elif request.method == "POST":
        username = request.form["username"].strip().lower()
        password = request.form["password"]

        with get_accounts() as conn:
            row = conn.execute("SELECT id, password, role, status FROM accounts WHERE uname = ?", (username,)).fetchone()
        
        error = None

        if row:
            if row["status"] != "active":
                error = "Dein Konto wartet noch auf eine Adminbestätigung"
            elif check_password_hash(row["password"], password):
                session.clear()
                
                user = User(row["id"], username, row["role"])
                login_user(user)

                return redirect("/")
            else:
                error = "Falsche Kombination aus Benutzernamen und Passwort."
        else:
            error = "Falsche Kombination aus Benutzernamen und Passwort."
        session.clear()
        return render_template("login.html", error=error)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    elif request.method == "POST":
        username = request.form["username"].strip().lower()
        password = request.form["password"]
        hashed_password = generate_password_hash(password)

        if not username or not password:
            session.clear()
            return render_template("register.html", error="Bitte Benutzername und Passwort eingeben.")

        with get_accounts() as conn:
            existing = conn.execute("SELECT id FROM accounts WHERE uname = ?", (username,)).fetchone()

            if existing:
                session.clear()
                return render_template("register.html", error="Benutzername existiert bereits.")

            conn.execute("INSERT INTO accounts (uname, password, role, status) VALUES (?, ?, ?, ?)",(username, hashed_password, 1, "pending"))
            conn.commit()
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