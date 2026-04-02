import datetime

from flask import Blueprint, render_template, request
from flask_login import current_user, login_required

from app.routes.auth import require_role
from app.utils import jugendgruppen_preview

index_bp = Blueprint("index", __name__)


@index_bp.route("/", methods=["GET"])
@login_required
@require_role(1)
def index():
    if request.method == "GET":
        user = current_user

        today = [
            "Montag",
            "Dienstag",
            "Mittwoch",
            "Donnerstag",
            "Freitag",
            "Samstag",
            "Sonntag",
        ][datetime.datetime.today().weekday()]

        heutige_gruppen = [g for g in jugendgruppen_preview() if g["wochentag"] == today]
        return render_template(
            "index.html", user=user, today=today, heutige_gruppen=heutige_gruppen
        )
