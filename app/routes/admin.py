from flask import Blueprint
from flask import session, redirect, url_for, request, render_template
from app.models import get_accounts, get_kompass
from app.routes.auth import check_user

import os
import json
from math import ceil

admin_bp = Blueprint('admin', __name__)

@admin_bp.route("/admin", methods=["GET", "POST"])
def admin():
    if not check_user(4):
        return redirect(url_for("auth.login"))

    # -------------------------
    # Handle account actions
    # -------------------------
    conn = get_accounts()
    cursor = conn.cursor()

    if request.method == "POST":
        account_id = request.form.get("account_id")
        action = request.form.get("action")
        new_role = request.form.get("new_role")

        if action == "approve":
            cursor.execute(
                "UPDATE accounts SET status='active' WHERE id=? AND rolls!='4'",
                (account_id,),
            )

        elif action == "delete":
            cursor.execute(
                "DELETE FROM accounts WHERE id=? AND rolls!='4'",
                (account_id,),
            )

        elif action == "change_role" and new_role in {"1", "2", "3", "4"}:
            cursor.execute(
                "UPDATE accounts SET rolls=? WHERE id=? AND rolls!='4'",
                (new_role, account_id),
            )

        conn.commit()

    accounts = cursor.execute(
        "SELECT id, uname, status, rolls FROM accounts ORDER BY id"
    ).fetchall()

    conn.close()

    # -------------------------
    # Load gruppenleiter data
    # -------------------------
    conn = get_kompass()
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

    conn.close()

    return render_template(
        "admin.html",
        accounts=accounts,
        gruppenleiter=gruppenleiter,
    )

@admin_bp.route("/gruppenleiter/add", methods=["GET", "POST"])
def add_gruppenleiter():
    if not check_user(4):
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        conn = get_kompass()
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
        conn.close()

    return redirect(url_for("admin.admin"))



@admin_bp.route("/gruppenleiter/<int:id>/edit", methods=["GET", "POST"])
def edit_gruppenleiter(id):
    if not check_user(4):
        return redirect(url_for("auth.login"))

    conn = get_kompass()
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
        conn.close()
        return redirect(url_for("admin.admin"))

    # GET -> Daten laden
    leiter = cursor.execute(
        "SELECT * FROM gruppenleiter WHERE id=?", (id,)
    ).fetchone()

    conn.close()
    return render_template("edit_gruppenleiter.html", leiter=leiter)