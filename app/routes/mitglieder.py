from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import login_required


from app.routes.auth import require_role
from app.services.mitglieder_service import *

mitglieder_bp = Blueprint("mitglieder", __name__)


@mitglieder_bp.route("/anmeldung", methods=["GET", "POST"])
def anmeldung():
    if request.method == "POST":
        add_mitglied_to_unapproved(request.form)
        return render_template("erfolg.html")

    return render_template("anmeldung.html")


@mitglieder_bp.route("/mitglieder", methods=["GET", "POST"])
@login_required
@require_role(3)
def mitglieder():
    if request.method == "POST":
        mitglied_id = request.form.get("mitglied_id")
        action = request.form.get("action")

        if not mitglied_id:
            return redirect(url_for("mitglieder.mitglieder"))
        if action == "approve":
            approve(mitglied_id)
        elif action == "reject":
            delete_unapproved(mitglied_id)

        return redirect(url_for("mitglieder.mitglieder"))

    mitglieder_daten = get_mitglieder_daten()
    mitglieder_unapproved_daten = get_unapproved_mitglieder_daten()

    return render_template(
        "mitglieder.html",
        mitglieder_unapproved_daten=mitglieder_unapproved_daten,
        mitglieder_daten=mitglieder_daten,
    )


@mitglieder_bp.route("/mitglied/<int:mitglied_id>/edit", methods=["GET", "POST"])
@login_required
@require_role(3)
def mitglied_bearbeiten(mitglied_id):
    if request.method == "POST":
        bearbeiten_form_data = request.form
        update_mitglied(mitglied_id, bearbeiten_form_data)
        return redirect(url_for("mitglieder.mitglieder"))

    mitglied = get_mitglieder_daten(mitglied_id=mitglied_id)
    erziehungsberechtigte = mitglied.get("erziehungsberechtigte", [])

    return render_template(
        "mitglied_bearbeiten.html",
        mitglied=mitglied,
        erziehungsberechtigte=erziehungsberechtigte,
    )
