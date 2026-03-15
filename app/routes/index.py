from flask import Blueprint
from flask import render_template, session, redirect, url_for, abort
import datetime
from app.models import get_accounts
from app.utils import jugendgruppen_preview
from flask_login import login_required, current_user
from app.routes.auth import require_role

index_bp = Blueprint('index', __name__)

@index_bp.route("/")
@login_required
@require_role(1)
def index():
    user = current_user

    today = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag","Samstag", "Sonntag"][datetime.datetime.today().weekday()]

    heutige_gruppen = [g for g in jugendgruppen_preview() if g["wochentag"] == today]
    return render_template("index.html", user=user, today=today, heutige_gruppen=heutige_gruppen)