from flask import Blueprint
from flask import request, render_template, session, redirect, url_for
from app.models import get_kompass
from app.routes.auth import check_user

mitgliederregistrierung_bp = Blueprint('mitgliederregistrierung', __name__)


@mitgliederregistrierung_bp.route("/anmeldung", methods=["GET", "POST"])
def anmeldung():
    if request.method == "GET":
        return render_template("anmeldung.html")

    # POST: Daten aus Formular
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

    unterschrift = request.form.get("unterschrift")

    with get_kompass() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO adressen_unapproved (strasse, hausnummer, plz, ort)
            VALUES (?, ?, ?, ?)
        """, (strasse, hausnummer, plz, ort))
        adresse_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO erziehungsberechtigte_unapproved (vorname, nachname, email, telefon, adresse_id)
            VALUES (?, ?, ?, ?, ?)
        """, (eb_vorname, eb_nachname, eb_email, eb_telefon, adresse_id))
        eb_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO mitglieder_unapproved (vorname, nachname, geburtsdatum, geschlecht, adresse_id, unterschrift)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (mitglied_vorname, mitglied_nachname, mitglied_geburtsdatum, mitglied_geschlecht, adresse_id, unterschrift))
        mitglied_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO mitglied_erziehungsberechtigte_unapproved (mitglied_id, erziehungsberechtigter_id, rolle)
            VALUES (?, ?, ?)
        """, (mitglied_id, eb_id, "Elternteil"))

        conn.commit()

    return render_template("erfolg.html")


@mitgliederregistrierung_bp.route("/mitglieder", methods=["GET", "POST"])
def mitglieder():
    if not check_user(3):
        return redirect(url_for("auth.login"))

    if request.method == "GET":
        with get_kompass() as conn:
            cursor = conn.cursor()

            # --- Unapproved ---
            cursor.execute("SELECT * FROM mitglieder_unapproved")
            mitglieder_unapproved = cursor.fetchall()

            mitglieder_unapproved_daten = []
            for mitglied in mitglieder_unapproved:
                mitglieder_unapproved_daten.append({
                    "id": mitglied["id"],
                    "vorname": mitglied["vorname"],
                    "nachname": mitglied["nachname"],
                    "geburtsdatum": mitglied["geburtsdatum"],
                    "unterschrift": mitglied["unterschrift"]
                })

            # --- Alle genehmigten Mitglieder mit Gruppen ---
            cursor.execute("""
                SELECT 
                    m.id,
                    m.vorname,
                    m.nachname,
                    m.geburtsdatum,
                    GROUP_CONCAT(j.name, ', ') as gruppen
                FROM mitglieder m
                LEFT JOIN mitglied_jugendgruppen mj 
                    ON m.id = mj.mitglied_id
                LEFT JOIN jugendgruppen j 
                    ON mj.jugendgruppe_id = j.id
                GROUP BY m.id
                ORDER BY m.nachname
            """)

            mitglieder = cursor.fetchall()
            mitglieder_daten = []
            for mitglied in mitglieder:
                mitglieder_daten.append({
                    "id": mitglied["id"],
                    "vorname": mitglied["vorname"],
                    "nachname": mitglied["nachname"],
                    "geburtsdatum": mitglied["geburtsdatum"],
                    "gruppen": mitglied["gruppen"]
                })

        return render_template(
            "mitglieder.html",
            mitglieder_unapproved_daten=mitglieder_unapproved_daten,
            mitglieder_daten=mitglieder_daten
        )

    elif request.method == "POST":
        mitglied_id = request.form.get("mitglied_id")
        action = request.form.get("action")

        if not mitglied_id:
            return redirect(url_for("mitgliederregistrierung.mitglieder"))

        with get_kompass() as conn:
            cursor = conn.cursor()

            # -----------------------------
            # Genehmigen
            # -----------------------------
            if action == "approve":

                cursor.execute("""
                    SELECT adresse_id
                    FROM mitglieder_unapproved
                    WHERE id = ?
                """, (mitglied_id,))
                adresse_id = cursor.fetchone()["adresse_id"]

                cursor.execute("""
                    INSERT INTO adressen (strasse, hausnummer, plz, ort)
                    SELECT strasse, hausnummer, plz, ort
                    FROM adressen_unapproved
                    WHERE id = ?
                """, (adresse_id,))
                adress_id_neu = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO mitglieder (vorname, nachname, geburtsdatum, geschlecht, adresse_id, unterschrift)
                    SELECT vorname, nachname, geburtsdatum, geschlecht, ?, unterschrift
                    FROM mitglieder_unapproved
                    WHERE id = ?
                """, (adress_id_neu, mitglied_id))
                mitglied_id_neu = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO erziehungsberechtigte (vorname, nachname, email, telefon, adresse_id)
                    SELECT vorname, nachname, email, telefon, ?
                    FROM erziehungsberechtigte_unapproved
                    WHERE id IN (
                        SELECT erziehungsberechtigter_id
                        FROM mitglied_erziehungsberechtigte_unapproved
                        WHERE mitglied_id = ?
                    )
                """, (adress_id_neu, mitglied_id))
                erziehungsberechtigter_id_neu = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO mitglied_erziehungsberechtigte (mitglied_id, erziehungsberechtigter_id, rolle)
                    SELECT ?, ?, rolle
                    FROM mitglied_erziehungsberechtigte_unapproved
                    WHERE mitglied_id = ?
                """, (mitglied_id_neu, erziehungsberechtigter_id_neu, mitglied_id))

                # Alte Daten löschen
                cursor.execute("""
                    DELETE FROM mitglied_erziehungsberechtigte_unapproved
                    WHERE mitglied_id = ?
                """, (mitglied_id,))

                cursor.execute("""
                    DELETE FROM erziehungsberechtigte_unapproved
                    WHERE id IN (
                        SELECT erziehungsberechtigter_id
                        FROM mitglied_erziehungsberechtigte_unapproved
                        WHERE mitglied_id = ?
                    )
                """, (mitglied_id,))

                cursor.execute("""
                    DELETE FROM adressen_unapproved
                    WHERE id = ?
                """, (adresse_id,))

                cursor.execute("""
                    DELETE FROM mitglieder_unapproved
                    WHERE id = ?
                """, (mitglied_id,))

            # -----------------------------
            # Ablehnen
            # -----------------------------
            elif action == "reject":

                cursor.execute("""
                    SELECT adresse_id
                    FROM mitglieder_unapproved
                    WHERE id = ?
                """, (mitglied_id,))
                adresse_id = cursor.fetchone()["adresse_id"]

                cursor.execute("""
                    DELETE FROM mitglied_erziehungsberechtigte_unapproved
                    WHERE mitglied_id = ?
                """, (mitglied_id,))

                cursor.execute("""
                    DELETE FROM erziehungsberechtigte_unapproved
                    WHERE id IN (
                        SELECT erziehungsberechtigter_id
                        FROM mitglied_erziehungsberechtigte_unapproved
                        WHERE mitglied_id = ?
                    )
                """, (mitglied_id,))

                cursor.execute("""
                    DELETE FROM adressen_unapproved
                    WHERE id = ?
                """, (adresse_id,))

                cursor.execute("""
                    DELETE FROM mitglieder_unapproved
                    WHERE id = ?
                """, (mitglied_id,))

            conn.commit()

        return redirect(url_for("mitgliederregistrierung.mitglieder"))


@mitgliederregistrierung_bp.route("/mitglied/<int:id>/edit", methods=["GET", "POST"])
def mitglied_bearbeiten(id):
    if not check_user(3):
        return redirect(url_for("auth.login"))

    with get_kompass() as conn:
        cursor = conn.cursor()

        # =========================
        # GET -> Daten laden
        # =========================
        if request.method == "GET":

            cursor.execute("""
                SELECT 
                    m.id,
                    m.vorname,
                    m.nachname,
                    m.geburtsdatum,
                    m.geschlecht,
                    m.adresse_id,
                    a.strasse,
                    a.hausnummer,
                    a.plz,
                    a.ort
                FROM mitglieder m
                LEFT JOIN adressen a
                ON m.adresse_id = a.id
                WHERE m.id = ?
            """, (id,))
            mitglied = cursor.fetchone()

            cursor.execute("""
                SELECT 
                    e.id,
                    e.vorname,
                    e.nachname,
                    e.email,
                    e.telefon,
                    me.rolle
                FROM erziehungsberechtigte e
                JOIN mitglied_erziehungsberechtigte me
                ON e.id = me.erziehungsberechtigter_id
                WHERE me.mitglied_id = ?
            """, (id,))
            erziehungsberechtigte = cursor.fetchall()

            return render_template(
                "mitglied_bearbeiten.html",
                mitglied=mitglied,
                erziehungsberechtigte=erziehungsberechtigte
            )

        # =========================
        # POST -> Daten speichern
        # =========================
        elif request.method == "POST":

            vorname = request.form.get("vorname")
            nachname = request.form.get("nachname")
            geburtsdatum = request.form.get("geburtsdatum")
            geschlecht = request.form.get("geschlecht")

            strasse = request.form.get("strasse")
            hausnummer = request.form.get("hausnummer")
            plz = request.form.get("plz")
            ort = request.form.get("ort")

            # -----------------
            # Mitglied update
            # -----------------
            cursor.execute("""
                UPDATE mitglieder
                SET
                    vorname = ?,
                    nachname = ?,
                    geburtsdatum = ?,
                    geschlecht = ?
                WHERE id = ?
            """, (vorname, nachname, geburtsdatum, geschlecht, id))

            # -----------------
            # Adresse update
            # -----------------
            cursor.execute("""
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
            """, (strasse, hausnummer, plz, ort, id))

            # -----------------
            # Eltern update
            # -----------------
            eb_ids = request.form.getlist("eb_id")
            eb_vornamen = request.form.getlist("eb_vorname")
            eb_nachnamen = request.form.getlist("eb_nachname")
            eb_emails = request.form.getlist("eb_email")
            eb_telefone = request.form.getlist("eb_telefon")

            for i in range(len(eb_ids)):
                cursor.execute("""
                    UPDATE erziehungsberechtigte
                    SET
                        vorname = ?,
                        nachname = ?,
                        email = ?,
                        telefon = ?
                    WHERE id = ?
                """, (
                    eb_vornamen[i],
                    eb_nachnamen[i],
                    eb_emails[i],
                    eb_telefone[i],
                    eb_ids[i]
                ))

            conn.commit()

            return redirect(url_for("mitgliederregistrierung.mitglieder"))