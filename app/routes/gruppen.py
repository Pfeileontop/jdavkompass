from flask import (
    Blueprint,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import login_required

from app.routes.auth import require_role
from app.services.utils import jugendgruppen_preview
from app.services.gruppen_service import *

gruppen_bp = Blueprint("gruppen", __name__)


@gruppen_bp.route("/gruppen", methods=["GET", "POST"])
@login_required
@require_role(1)
def gruppen():
    gruppen = jugendgruppen_preview()
    return render_template("gruppen.html", gruppen=gruppen)


@gruppen_bp.route("/gruppen/neue", methods=["POST"])
@login_required
@require_role(3)
def neue_gruppe():
    data = request.form
    neue_gruppe_erstellen(data)
    return redirect(url_for("gruppen.gruppen"))


@gruppen_bp.route("/gruppen/<int:gruppe_id>/loeschen", methods=["POST"])
@login_required
@require_role(3)
def gruppe_loeschen(gruppe_id):
    loesche_gruppe(gruppe_id)
    return redirect(url_for("gruppen.gruppen"))
