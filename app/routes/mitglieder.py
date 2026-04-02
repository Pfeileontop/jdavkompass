from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import login_required

from app.models import get_kompass
from app.routes.auth import require_role

mitglieder_bp = Blueprint("mitglieder", __name__)


@mitglieder_bp.route("/anmeldung", methods=["GET", "POST"])
def anmeldung():
    if request.method == "GET":
        return render_template("anmeldung.html")

    if request.method == "POST":
        mitglied_vorname = request.form.get("mitglied_vorname")
        mitglied_nachname = request.form.get("mitglied_nachname")
        mitglied_geburtsdatum = request.form.get("mitglied_geburtsdatum")
        mitglied_geschlecht = request.form.get("mitglied_geschlecht")

        strasse = request.form.get("strasse")
        hausnummer = request.form.get("hausnummer")
        plz = request.form.get("plz")
        ort = request.form.get("ort")

        eb_vorname = request.form.get("eb_vorname")
        eb_nachname = request.form.get("eb_nachname")
        eb_email = request.form.get("eb_email")
        eb_telefon = request.form.get("eb_telefon")

        mitgliedschaft = request.form.get("mitgliedschaft_bestaetigt")
        beitraege = request.form.get("beitraege_bestaetigt")
        unterschrift = request.form.get("unterschrift")

        with get_kompass() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO adressen_unapproved (strasse, hausnummer, plz, ort)
                VALUES (?, ?, ?, ?)
            """,
                (strasse, hausnummer, plz, ort),
            )
            adresse_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO erziehungsberechtigte_unapproved (vorname, nachname, email, telefon, adresse_id)
                VALUES (?, ?, ?, ?, ?)
            """,
                (eb_vorname, eb_nachname, eb_email, eb_telefon, adresse_id),
            )
            eb_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO mitglieder_unapproved (vorname, nachname, geburtsdatum, geschlecht, adresse_id, unterschrift, mitgliedschaft, beitraege)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    mitglied_vorname,
                    mitglied_nachname,
                    mitglied_geburtsdatum,
                    mitglied_geschlecht,
                    adresse_id,
                    unterschrift,
                    mitgliedschaft,
                    beitraege,
                ),
            )
            mitglied_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO mitglied_erziehungsberechtigte_unapproved (mitglied_id, erziehungsberechtigter_id)
                VALUES (?, ?)
            """,
                (mitglied_id, eb_id),
            )

            conn.commit()

    return render_template("erfolg.html")


def get_mitglieder_daten(mitglied_id=None, unterschrift=False):
    with get_kompass() as conn:
        cursor = conn.cursor()

        select_fields = "m.id, m.vorname, m.nachname, m.geburtsdatum, m.geschlecht, m.adresse_id, m.mitgliedsnummer"
        if unterschrift:
            select_fields += ", m.unterschrift"
        sql = f"""
        SELECT
            {select_fields},
            a.strasse, a.hausnummer, a.plz, a.ort
        FROM mitglieder m
        LEFT JOIN adressen a ON m.adresse_id = a.id
        """
        params = ()
        if mitglied_id is not None:
            sql += " WHERE m.id = ?"
            params = (mitglied_id,)

        cursor.execute(sql, params)
        mitglieder_rows = cursor.fetchall()
        mitglieder_daten = []

        for m in mitglieder_rows:
            m_dict = dict(m)
            cursor.execute(
                """
                SELECT j.*
                FROM jugendgruppen j
                JOIN mitglied_jugendgruppen mj ON j.id = mj.jugendgruppe_id
                WHERE mj.mitglied_id = ?
            """,
                (m["id"],),
            )
            gruppen = [dict(row) for row in cursor.fetchall()]

            cursor.execute(
                """
                SELECT e.*
                FROM erziehungsberechtigte e
                JOIN mitglied_erziehungsberechtigte me ON e.id = me.erziehungsberechtigter_id
                WHERE me.mitglied_id = ?
                LIMIT 1
            """,
                (m["id"],),
            )
            erziehungsberechtigte_row = cursor.fetchone()
            erziehungsberechtigte = (
                dict(erziehungsberechtigte_row) if erziehungsberechtigte_row else None
            )

            mitglieder_daten.append(
                {
                    **m_dict,
                    "gruppen": gruppen,
                    "erziehungsberechtigte": erziehungsberechtigte,
                }
            )

    if mitglied_id is not None:
        return mitglieder_daten[0] if mitglieder_daten else None

    return mitglieder_daten


def get_unapproved_mitglieder_daten():
    with get_kompass() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                m.id, m.vorname, m.nachname, m.geburtsdatum, m.geschlecht,
                m.unterschrift, m.mitgliedschaft, m.beitraege,
                a.strasse, a.hausnummer, a.plz, a.ort
            FROM mitglieder_unapproved m
            LEFT JOIN adressen_unapproved a ON m.adresse_id = a.id
            ORDER BY m.nachname
        """)

        mitglieder_rows = cursor.fetchall()
        mitglieder_unapproved_daten = []

        for m in mitglieder_rows:
            m_dict = dict(m)

            cursor.execute(
                """
                SELECT e.*
                FROM erziehungsberechtigte_unapproved e
                JOIN mitglied_erziehungsberechtigte_unapproved me
                  ON e.id = me.erziehungsberechtigter_id
                WHERE me.mitglied_id = ?
                LIMIT 1
            """,
                (m["id"],),
            )
            eb_row = cursor.fetchone()
            erziehungsberechtigte = dict(eb_row) if eb_row else None

            mitglieder_unapproved_daten.append(
                {**m_dict, "erziehungsberechtigte": erziehungsberechtigte}
            )

    return mitglieder_unapproved_daten


def delete_unapproved(cursor, mitglied_id):
    cursor.execute(
        "SELECT adresse_id FROM mitglieder_unapproved WHERE id = ?", (mitglied_id,)
    )
    adresse_id = cursor.fetchone()["adresse_id"]

    cursor.execute(
        "DELETE FROM mitglied_erziehungsberechtigte_unapproved WHERE mitglied_id = ?",
        (mitglied_id,),
    )

    cursor.execute(
        """
        DELETE FROM erziehungsberechtigte_unapproved
        WHERE id IN (
            SELECT erziehungsberechtigter_id
            FROM mitglied_erziehungsberechtigte_unapproved
            WHERE mitglied_id = ?
        )
        """,
        (mitglied_id,),
    )

    cursor.execute("DELETE FROM adressen_unapproved WHERE id = ?", (adresse_id,))
    cursor.execute("DELETE FROM mitglieder_unapproved WHERE id = ?", (mitglied_id,))


@mitglieder_bp.route("/mitglieder", methods=["GET", "POST"])
@login_required
@require_role(3)
def mitglieder():
    if request.method == "GET":
        mitglieder_daten = get_mitglieder_daten()
        mitglieder_unapproved_daten = get_unapproved_mitglieder_daten()

        return render_template(
            "mitglieder.html",
            mitglieder_unapproved_daten=mitglieder_unapproved_daten,
            mitglieder_daten=mitglieder_daten,
        )

    if request.method == "POST":
        mitglied_id = request.form.get("mitglied_id")
        action = request.form.get("action")

        if not mitglied_id:
            return redirect(url_for("mitglieder.mitglieder"))

        with get_kompass() as conn:
            cursor = conn.cursor()
            if action == "approve":

                cursor.execute(
                    """
                    SELECT adresse_id
                    FROM mitglieder_unapproved
                    WHERE id = ?
                """,
                    (mitglied_id,),
                )
                adresse_id = cursor.fetchone()["adresse_id"]

                cursor.execute(
                    """
                    INSERT INTO adressen (strasse, hausnummer, plz, ort)
                    SELECT strasse, hausnummer, plz, ort
                    FROM adressen_unapproved
                    WHERE id = ?
                """,
                    (adresse_id,),
                )
                adress_id_neu = cursor.lastrowid

                cursor.execute(
                    """
                    INSERT INTO mitglieder (vorname, nachname, geburtsdatum, geschlecht, adresse_id, unterschrift)
                    SELECT vorname, nachname, geburtsdatum, geschlecht, ?, unterschrift
                    FROM mitglieder_unapproved
                    WHERE id = ?
                """,
                    (adress_id_neu, mitglied_id),
                )
                mitglied_id_neu = cursor.lastrowid

                cursor.execute(
                    """
                    INSERT INTO erziehungsberechtigte (vorname, nachname, email, telefon, adresse_id)
                    SELECT vorname, nachname, email, telefon, ?
                    FROM erziehungsberechtigte_unapproved
                    WHERE id IN (
                        SELECT erziehungsberechtigter_id
                        FROM mitglied_erziehungsberechtigte_unapproved
                        WHERE mitglied_id = ?
                    )
                """,
                    (adress_id_neu, mitglied_id),
                )
                erziehungsberechtigter_id_neu = cursor.lastrowid

                cursor.execute(
                    """
                    INSERT INTO mitglied_erziehungsberechtigte (mitglied_id, erziehungsberechtigter_id, rolle)
                    SELECT ?, ?, rolle
                    FROM mitglied_erziehungsberechtigte_unapproved
                    WHERE mitglied_id = ?
                """,
                    (mitglied_id_neu, erziehungsberechtigter_id_neu, mitglied_id),
                )

                delete_unapproved(cursor, mitglied_id)

            elif action == "reject":

                delete_unapproved(cursor, mitglied_id)

            conn.commit()

        return redirect(url_for("mitglieder.mitglieder"))


@mitglieder_bp.route("/mitglied/<int:id>/edit", methods=["GET", "POST"])
@login_required
@require_role(3)
def mitglied_bearbeiten(id):
    if request.method == "GET":
        mitglied = get_mitglieder_daten(mitglied_id=id)
        erziehungsberechtigte = mitglied.get("erziehungsberechtigte", [])

        return render_template(
            "mitglied_bearbeiten.html",
            mitglied=mitglied,
            erziehungsberechtigte=erziehungsberechtigte,
        )

    if request.method == "POST":
        with get_kompass() as conn:
            cursor = conn.cursor()

            vorname = request.form.get("vorname")
            nachname = request.form.get("nachname")
            geburtsdatum = request.form.get("geburtsdatum")
            geschlecht = request.form.get("geschlecht")
            mitgliedsnummer = request.form.get("mitgliedsnummer")
            strasse = request.form.get("strasse")
            hausnummer = request.form.get("hausnummer")
            plz = request.form.get("plz")
            ort = request.form.get("ort")
            eb_id = request.form.get("eb_id")
            eb_vorname = request.form.get("eb_vorname")
            eb_nachname = request.form.get("eb_nachname")
            eb_email = request.form.get("eb_email")
            eb_telefon = request.form.get("eb_telefon")

            cursor.execute(
                """
                UPDATE mitglieder
                SET
                    vorname = ?,
                    nachname = ?,
                    geburtsdatum = ?,
                    geschlecht = ?,
                    mitgliedsnummer = ?
                WHERE id = ?
            """,
                (vorname, nachname, geburtsdatum, geschlecht, mitgliedsnummer, id),
            )

            cursor.execute(
                """
                UPDATE adressen
                SET
                    strasse = ?,
                    hausnummer = ?,
                    plz = ?,
                    ort = ?
                WHERE id = (
                    SELECT adresse_id
                    FROM mitglieder
                    WHERE id = ?
                )
            """,
                (strasse, hausnummer, plz, ort, id),
            )

            cursor.execute(
                """
                UPDATE erziehungsberechtigte
                SET
                    vorname = ?,
                    nachname = ?,
                    email = ?,
                    telefon = ?
                WHERE id = ?
            """,
                (
                    eb_vorname,
                    eb_nachname,
                    eb_email,
                    eb_telefon,
                    eb_id,
                ),
            )

            conn.commit()

        return redirect(url_for("mitglieder.mitglieder"))
