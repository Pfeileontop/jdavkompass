from flask import Blueprint
from flask import render_template, session, redirect, url_for, abort
import datetime
from app.models import get_accounts
from app.utils import jugendgruppen_preview
from app.routes.auth import check_user

index_bp = Blueprint('index', __name__)


@index_bp.route("/")
def index():
    if not check_user(1):
        abort(403)

    with get_accounts() as conn:
        user = conn.execute("SELECT id, uname FROM accounts WHERE id = ?", (session["user_id"],)).fetchone()

    today = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag","Samstag", "Sonntag"][datetime.datetime.today().weekday()]

    heutige_gruppen = [g for g in jugendgruppen_preview() if g["wochentag"] == today]
    return render_template("index.html", user=user, today=today, heutige_gruppen=heutige_gruppen)