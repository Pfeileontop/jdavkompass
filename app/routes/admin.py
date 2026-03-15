from flask import Blueprint
from flask import session, redirect, url_for, request, render_template, abort
from app.models import get_accounts, get_kompass
from flask_login import login_required, current_user
from app.routes.auth import require_role

import os
import json
from math import ceil

admin_bp = Blueprint('admin', __name__)

@admin_bp.route("/admin", methods=["GET", "POST"])
@login_required
@require_role(4)
def admin():
    # -------------------------
    # Handle account actions
    # -------------------------
    with get_accounts() as conn:
        cursor = conn.cursor()

        if request.method == "POST":
            account_id = request.form.get("account_id")
            action = request.form.get("action")
            new_role = request.form.get("new_role")

            if action == "approve":
                cursor.execute(
                    "UPDATE accounts SET status='active' WHERE id=? AND role!='4'",
                    (account_id,),
                )

            elif action == "delete":
                cursor.execute(
                    "DELETE FROM accounts WHERE id=? AND role!='4'",
                    (account_id,),
                )

            elif action == "change_role" and new_role in {"1", "2", "3", "4"}:
                cursor.execute(
                    "UPDATE accounts SET role=? WHERE id=? AND role!='4'",
                    (new_role, account_id),
                )

            conn.commit()

        accounts = cursor.execute(
            "SELECT id, uname, status, role FROM accounts ORDER BY id"
        ).fetchall()

    # -------------------------
    # Load gruppenleiter data
    # -------------------------
    with get_kompass() as conn:
        cursor = conn.cursor()

        gruppenleiter = cursor.execute("""
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
        """).fetchall()

    return render_template(
        "admin.html",
        accounts=accounts,
        gruppenleiter=gruppenleiter,
    )

@admin_bp.route("/gruppenleiter/add", methods=["GET", "POST"])
@login_required
@require_role(4)
def add_gruppenleiter():
    if request.method == "POST":
        with get_kompass() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO gruppenleiter 
                (vorname, nachname, geburtsdatum, iban, bic, bank, telefon, gruppenrolle, vereinsrolle)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request.form["vorname"],
                request.form["nachname"],
                request.form["geburtsdatum"],
                request.form["iban"],
                request.form["bic"],
                request.form["bank"],
                request.form["telefon"],
                request.form["gruppenrolle"],
                request.form["vereinsrolle"]
            ))
            conn.commit()

    return redirect(url_for("admin.admin"))



@admin_bp.route("/gruppenleiter/<int:id>/edit", methods=["GET", "POST"])
@login_required
@require_role(4)
def gruppenleiter_bearbeiten(id):
    with get_kompass() as conn:
        cursor = conn.cursor()

        if request.method == "POST":
            cursor.execute("""
                UPDATE gruppenleiter
                SET vorname=?, nachname=?, geburtsdatum=?, iban=?, bic=?, bank=?,
                    telefon=?, gruppenrolle=?, vereinsrolle=?
                WHERE id=?
            """, (
                request.form["vorname"],
                request.form["nachname"],
                request.form["geburtsdatum"],
                request.form["iban"],
                request.form["bic"],
                request.form["bank"],
                request.form["telefon"],
                request.form["gruppenrolle"],
                request.form["vereinsrolle"],
                id
            ))
            conn.commit()
            return redirect(url_for("admin.admin"))

        # GET -> Daten laden
        leiter = cursor.execute(
            "SELECT * FROM gruppenleiter WHERE id=?", (id,)
        ).fetchone()

    return render_template("gruppenleiter_bearbeiten.html", leiter=leiter)