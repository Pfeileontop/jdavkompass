from flask import Blueprint, render_template
from flask_login import current_user, login_required

from app.routes.auth import require_role
from app.services.utils import jugendgruppen_preview, heute

from flask import send_from_directory
import os

index_bp = Blueprint("index", __name__)


@index_bp.route("/", methods=["GET"])
@login_required
@require_role(1)
def index():
    """Zeigt die Hauptseite für alle eingeloggten Nutzer,
    die mindestens Rolle 1 haben an.

    Returns:
        Response: HTML Template "index.html" mit den Variablen
        fuer den aktuellen Nutzer (current_user), dem heutigen Tag
        und den Gruppen die heute stattfinden.
    """
    heutige_gruppen = [g for g in jugendgruppen_preview() if g["wochentag"] == heute()]

    return render_template(
        "index.html", user=current_user, today=heute(), heutige_gruppen=heutige_gruppen
    )


@index_bp.route("/download/<path:file>", methods=["GET"])
@login_required
@require_role(1)
def download(file):
    upload_folder = os.path.join(os.getcwd(), "uploads")
    return send_from_directory(upload_folder, file, as_attachment=True)
