from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import login_required

from app.routes.auth import require_role
from app.services.admin_service import *

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin", methods=["GET", "POST"])
@login_required
@require_role(4)
def admin():
    if request.method == "POST":
        account_id = request.form.get("account_id")
        action = request.form.get("action")
        new_role = request.form.get("new_role")

        if action == "approve":
            update_account_status(account_id, "active")
        elif action == "delete":
            delete_account(account_id)
        elif action == "change_role" and new_role in {"1", "2", "3", "4"}:
            change_account_role(account_id, new_role)

        return redirect(url_for("admin.admin"))

    return render_template(
        "admin.html",
        accounts=get_all_accounts(),
        gruppenleiter=get_all_gruppenleiter(),
    )


@admin_bp.route("/gruppenleiter/add", methods=["POST"])
@login_required
@require_role(4)
def add_gruppenleiter():
    save_gruppenleiter(request.form, None)
    return redirect(url_for("admin.admin"))


@admin_bp.route("/gruppenleiter/<int:gruppenleiter_id>/edit", methods=["GET", "POST"])
@login_required
@require_role(4)
def gruppenleiter_bearbeiten(gruppenleiter_id):
    if request.method == "POST":
        save_gruppenleiter(request.form, gruppenleiter_id)
        return redirect(url_for("admin.admin"))

    gruppenleiter = get_gruppenleiter(gruppenleiter_id)
    return render_template("gruppenleiter_bearbeiten.html", leiter=gruppenleiter)
