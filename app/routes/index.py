from flask import Blueprint, render_template, request
from flask_login import current_user, login_required

from app.routes.auth import require_role
from app.services.utils import jugendgruppen_preview, heute

index_bp = Blueprint("index", __name__)


@index_bp.route("/", methods=["GET"])
@login_required
@require_role(1)
def index():
    heutige_gruppen = [g for g in jugendgruppen_preview() if g["wochentag"] == heute()]

    return render_template(
        "index.html", user=current_user, today=heute(), heutige_gruppen=heutige_gruppen
    )
