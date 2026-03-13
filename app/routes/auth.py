from flask import Blueprint
from flask import request, render_template, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import get_accounts
import sqlite3

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    elif request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_accounts()
        row = conn.execute("SELECT id, password, rolls, status FROM accounts WHERE uname = ?", (username,)).fetchone()
        conn.close()
        error = None

        if row:
            if row["status"] != "active":
                error = "Dein Konto wartet noch auf eine Adminbestätigung"
            elif check_password_hash(row["password"], password):
                session.clear()
                session["user_id"] = row["id"]
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
        username = request.form["username"]
        password = request.form["password"]
        hashed_password = generate_password_hash(password)

        if not username or not password:
            session.clear()
            return render_template("register.html", error="Bitte Benutzername und Passwort eingeben.")

        conn = get_accounts()
        existing = conn.execute("SELECT id FROM accounts WHERE uname = ?", (username,)).fetchone()

        if existing:
            session.clear()
            return render_template("register.html", error="Benutzername existiert bereits.")

        conn.execute("INSERT INTO accounts (uname, password, rolls) VALUES (?, ?, ?)", (username, hashed_password, "requesting access"))
        conn.commit()

        conn.close()
        return redirect("/")


@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


def check_user(level):
    if "user_id" not in session:
        session.clear()
        return False

    role_levels = {
        1: "view_only",  # Level 1: View only
        2: "attendance_modify",  # Level 2: Modify attendance, add leaders
        3: "member_manage",  # Level 3: Manage members, delete groups, create new groups
        4: "admin"  # Admin: Full access
    }

    con = sqlite3.connect("app/db/accounts.db")
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    id = session.get("user_id")
    cur.execute("SELECT rolls FROM accounts WHERE id = ?", (id,))
    role = int(cur.fetchone()["rolls"])

    if role in role_levels and role >= level:
        return True

    return False
