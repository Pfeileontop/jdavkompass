from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import login_required

from app.models import get_accounts, get_kompass
from app.routes.auth import require_role

admin_bp = Blueprint("admin", __name__)


def update_account_status(conn, account_id, status):
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE accounts SET status=? WHERE id=? AND role!='4'",
        (status, account_id),
    )


def delete_account(conn, account_id):
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM accounts WHERE id=? AND role!='4'",
        (account_id,),
    )


def change_account_role(conn, account_id, new_role):
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE accounts SET role=? WHERE id=? AND role!='4'",
        (new_role, account_id),
    )


def save_gruppenleiter(conn, data, id):
    cursor = conn.cursor()
    if id:
        cursor.execute(
            """
            UPDATE gruppenleiter
            SET
                vorname=?, nachname=?, geburtsdatum=?, iban=?, bic=?,
                bank=?, telefon=?, gruppenrolle=?, vereinsrolle=?
            WHERE id=?
            """,
            (
                data["vorname"],
                data["nachname"],
                data["geburtsdatum"],
                data["iban"],
                data["bic"],
                data["bank"],
                data["telefon"],
                data["gruppenrolle"],
                data["vereinsrolle"],
                id,
            ),
        )

    else:
        cursor.execute(
            """
            INSERT INTO gruppenleiter (
                vorname, nachname, geburtsdatum, iban, bic, bank,
                telefon, gruppenrolle, vereinsrolle
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["vorname"],
                data["nachname"],
                data["geburtsdatum"],
                data["iban"],
                data["bic"],
                data["bank"],
                data["telefon"],
                data["gruppenrolle"],
                data["vereinsrolle"],
            ),
        )


@admin_bp.route("/admin", methods=["GET", "POST"])
@login_required
@require_role(4)
def admin():
    print(request)
    if request.method == "GET":
        with get_kompass() as conn:
            cursor = conn.cursor()

            gruppenleiter = cursor.execute(
                """
                SELECT
                    gl.id,
                    gl.vorname,
                    gl.nachname,
                    gl.geburtsdatum,
                    gl.iban,
                    gl.bic,
                    gl.bank,
                    gl.telefon,
                    gl.gruppenrolle,
                    gl.vereinsrolle,
                    GROUP_CONCAT(jg.name, ', ') AS jugendgruppen
                FROM gruppenleiter gl
                LEFT JOIN gruppenleiter_jugendgruppen gj
                    ON gl.id = gj.gruppenleiter_id
                LEFT JOIN jugendgruppen jg
                    ON gj.jugendgruppe_id = jg.id
                GROUP BY gl.id
                ORDER BY gl.nachname
                """
            ).fetchall()

        with get_accounts() as conn:
            cursor = conn.cursor()
            accounts = cursor.execute(
                "SELECT id, uname, status, role FROM accounts ORDER BY id"
            ).fetchall()

        return render_template(
            "admin.html",
            accounts=accounts,
            gruppenleiter=gruppenleiter,
        )

    else:
        with get_accounts() as conn:
            account_id = request.form.get("account_id")
            action = request.form.get("action")
            new_role = request.form.get("new_role")

            if action == "approve":
                update_account_status(conn, account_id, "active")
            elif action == "delete":
                delete_account(conn, account_id)
            elif action == "change_role" and new_role in {"1", "2", "3", "4"}:
                change_account_role(conn, account_id, new_role)
        return redirect(url_for("admin.admin"))


@admin_bp.route("/gruppenleiter/add", methods=["POST"])
@login_required
@require_role(4)
def add_gruppenleiter():
    if request.method == "POST":
        with get_kompass() as conn:
            save_gruppenleiter(conn, request.form, None)

        return redirect(url_for("admin.admin"))


@admin_bp.route("/gruppenleiter/<int:id>/edit", methods=["GET", "POST"])
@login_required
@require_role(4)
def gruppenleiter_bearbeiten(id):
    if request.method == "GET":
        with get_kompass() as conn:
            cursor = conn.cursor()
            leiter = cursor.execute(
                "SELECT * FROM gruppenleiter WHERE id=?", (id,)
            ).fetchone()

        return render_template("gruppenleiter_bearbeiten.html", leiter=leiter)

    else:
        with get_kompass() as conn:
            save_gruppenleiter(conn, request.form, id)

        return redirect(url_for("admin.admin"))
