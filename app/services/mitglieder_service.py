from app.models import get_kompass


def get_unapproved_mitglieder_daten():
    with get_kompass() as conn:
        conn.row_factory = lambda cursor, row: {
            col[0]: row[idx] for idx, col in enumerate(cursor.description)
        }
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                m.id,
                m.vorname,
                m.nachname,
                m.geburtsdatum,
                m.geschlecht,
                m.unterschrift,
                m.mitgliedschaft,
                m.beitraege,
                m.datenschutz,
                m.bilder,
                m.richtigkeit,
                a.strasse,
                a.hausnummer,
                a.plz,
                a.ort,
                e.id AS eb_id,
                e.vorname AS eb_vorname,
                e.nachname AS eb_nachname,
                e.email AS eb_email,
                e.telefon AS eb_telefon
            FROM
                mitglieder_unapproved m
                LEFT JOIN adressen_unapproved a ON m.adresse_id = a.id
                LEFT JOIN mitglied_erziehungsberechtigte_unapproved me ON m.id = me.mitglied_id
                LEFT JOIN erziehungsberechtigte_unapproved e ON me.erziehungsberechtigter_id = e.id
            ORDER BY
                m.nachname
            """)

        rows = cursor.fetchall()

        mitglieder_unapproved_daten = []
        for row in rows:
            erziehungsberechtigte = None
            if row.get("eb_id") is not None:
                erziehungsberechtigte = {
                    "id": row.pop("eb_id"),
                    "vorname": row.pop("eb_vorname"),
                    "nachname": row.pop("eb_nachname"),
                    "email": row.pop("eb_email"),
                    "telefon": row.pop("eb_telefon"),
                }
            mitglieder_unapproved_daten.append(
                {**row, "erziehungsberechtigte": erziehungsberechtigte}
            )

    return mitglieder_unapproved_daten


def delete_unapproved(mitglied_id):
    with get_kompass() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT adresse_id FROM mitglieder_unapproved WHERE id = ?", (mitglied_id,)
        )
        adresse_id = cursor.fetchone()["adresse_id"]

        cursor.execute(
            """
            DELETE FROM mitglied_erziehungsberechtigte_unapproved
            WHERE
                mitglied_id = ?
            """,
            (mitglied_id,),
        )

        cursor.execute(
            """
            DELETE FROM erziehungsberechtigte_unapproved
            WHERE
                id IN (
                    SELECT
                        erziehungsberechtigter_id
                    FROM
                        mitglied_erziehungsberechtigte_unapproved
                    WHERE
                        mitglied_id = ?
                    )
            """,
            (mitglied_id,),
        )

        cursor.execute(
            """
            DELETE FROM adressen_unapproved
            WHERE
                id = ?
            """,
            (adresse_id,)
        )
        cursor.execute(
            """
            DELETE FROM mitglieder_unapproved
            WHERE
                id = ?
            """,
            (mitglied_id,)
        )


def add_mitglied_to_unapproved(anmeldung_form_data):
    mitglied_vorname = anmeldung_form_data.get("mitglied_vorname")
    mitglied_nachname = anmeldung_form_data.get("mitglied_nachname")
    mitglied_geburtsdatum = anmeldung_form_data.get("mitglied_geburtsdatum")
    mitglied_geschlecht = anmeldung_form_data.get("mitglied_geschlecht")
    strasse = anmeldung_form_data.get("strasse")
    hausnummer = anmeldung_form_data.get("hausnummer")
    plz = anmeldung_form_data.get("plz")
    ort = anmeldung_form_data.get("ort")
    eb_vorname = anmeldung_form_data.get("eb_vorname")
    eb_nachname = anmeldung_form_data.get("eb_nachname")
    eb_email = anmeldung_form_data.get("eb_email")
    eb_telefon = anmeldung_form_data.get("eb_telefon")
    mitgliedschaft = anmeldung_form_data.get("mitgliedschaft_bestaetigt")
    beitraege = anmeldung_form_data.get("beitraege_bestaetigt")
    datenschutz = anmeldung_form_data.get("datenschutz_bestaetigt")
    bilder = anmeldung_form_data.get("bilder_bestaetigt")
    richtigkeit = anmeldung_form_data.get("richtigkeit_bestaetigt")
    unterschrift = anmeldung_form_data.get("unterschrift")

    with get_kompass() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO
                adressen_unapproved (strasse, hausnummer, plz, ort)
            VALUES
                (?, ?, ?, ?)
            """,
            (strasse, hausnummer, plz, ort),
        )
        adresse_id = cursor.lastrowid
        cursor.execute(
            """
            INSERT INTO
                erziehungsberechtigte_unapproved (vorname, nachname, email, telefon, adresse_id)
            VALUES
                (?, ?, ?, ?, ?)
            """,
            (eb_vorname, eb_nachname, eb_email, eb_telefon, adresse_id),
        )
        eb_id = cursor.lastrowid
        cursor.execute(
            """
            INSERT INTO
                mitglieder_unapproved (
                    vorname,
                    nachname,
                    geburtsdatum,
                    geschlecht,
                    adresse_id,
                    unterschrift,
                    mitgliedschaft,
                    beitraege,
                    datenschutz,
                    bilder,
                    richtigkeit
                )
            VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                datenschutz,
                bilder,
                richtigkeit,
            ),
        )
        mitglied_id = cursor.lastrowid
        cursor.execute(
            """
            INSERT INTO
                mitglied_erziehungsberechtigte_unapproved (mitglied_id, erziehungsberechtigter_id)
            VALUES
                (?, ?)
            """,
            (mitglied_id, eb_id),
        )


def approve_unapproved(mitglied_id):
    with get_kompass() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                adresse_id
            FROM
                mitglieder_unapproved
            WHERE
                id = ?
            """,
            (mitglied_id,),
        )
        adresse_id = cursor.fetchone()["adresse_id"]

        cursor.execute(
            """
            INSERT INTO
                adressen (strasse, hausnummer, plz, ort)
            SELECT
                strasse,
                hausnummer,
                plz,
                ort
            FROM
                adressen_unapproved
            WHERE
                id = ?
            """,
            (adresse_id,),
        )
        adress_id_neu = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO
                mitglieder (
                    vorname,
                    nachname,
                    geburtsdatum,
                    geschlecht,
                    adresse_id,
                    bilder,
                    unterschrift
                )
            SELECT
                vorname,
                nachname,
                geburtsdatum,
                geschlecht,
                ?,
                bilder,
                unterschrift
            FROM
                mitglieder_unapproved
            WHERE
                id = ?
            """,
            (adress_id_neu, mitglied_id),
        )
        mitglied_id_neu = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO
                erziehungsberechtigte (vorname, nachname, email, telefon, adresse_id)
            SELECT
                vorname,
                nachname,
                email,
                telefon,
                ?
            FROM
                erziehungsberechtigte_unapproved
            WHERE
                id IN (
                    SELECT
                        erziehungsberechtigter_id
                    FROM
                        mitglied_erziehungsberechtigte_unapproved
                    WHERE
                        mitglied_id = ?
                )
            """,
            (adress_id_neu, mitglied_id),
        )
        erziehungsberechtigter_id_neu = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO
                mitglied_erziehungsberechtigte (mitglied_id, erziehungsberechtigter_id, rolle)
            SELECT
                ?,
                ?,
                rolle
            FROM
                mitglied_erziehungsberechtigte_unapproved
            WHERE
                mitglied_id = ?
            """,
            (mitglied_id_neu, erziehungsberechtigter_id_neu, mitglied_id),
        )


def approve(mitglied_id):
    approve_unapproved(mitglied_id)
    delete_unapproved(mitglied_id)


def get_mitglieder_daten(mitglied_id=None, unterschrift=False):
    with get_kompass() as conn:
        cursor = conn.cursor()

        select_fields = "m.id, m.vorname, m.nachname, m.geburtsdatum, m.geschlecht, m.adresse_id, m.mitgliedsnummer"
        if unterschrift:
            select_fields += ", m.unterschrift"
        sql = f"""
            SELECT
                {select_fields},
                a.strasse,
                a.hausnummer,
                a.plz,
                a.ort
            FROM
                mitglieder m
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
                SELECT
                    j.*
                FROM
                    jugendgruppen j
                    JOIN mitglied_jugendgruppen mj ON j.id = mj.jugendgruppe_id
                WHERE
                    mj.mitglied_id = ?
                """,
                (m["id"],),
            )
            gruppen = [dict(row) for row in cursor.fetchall()]

            cursor.execute(
                """
                SELECT
                    e.*
                FROM
                    erziehungsberechtigte e
                    JOIN mitglied_erziehungsberechtigte me ON e.id = me.erziehungsberechtigter_id
                WHERE
                    me.mitglied_id = ?
                LIMIT
                    1
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


def update_mitglied(mitglied_id, bearbeiten_form_data):
    vorname = bearbeiten_form_data.get("vorname")
    nachname = bearbeiten_form_data.get("nachname")
    geburtsdatum = bearbeiten_form_data.get("geburtsdatum")
    geschlecht = bearbeiten_form_data.get("geschlecht")
    mitgliedsnummer = bearbeiten_form_data.get("mitgliedsnummer")
    strasse = bearbeiten_form_data.get("strasse")
    hausnummer = bearbeiten_form_data.get("hausnummer")
    plz = bearbeiten_form_data.get("plz")
    ort = bearbeiten_form_data.get("ort")
    eb_id = bearbeiten_form_data.get("eb_id")
    eb_vorname = bearbeiten_form_data.get("eb_vorname")
    eb_nachname = bearbeiten_form_data.get("eb_nachname")
    eb_email = bearbeiten_form_data.get("eb_email")
    eb_telefon = bearbeiten_form_data.get("eb_telefon")
    with get_kompass() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE mitglieder
            SET
                vorname = ?,
                nachname = ?,
                geburtsdatum = ?,
                geschlecht = ?,
                mitgliedsnummer = ?
            WHERE
                id = ?
            """,
            (vorname, nachname, geburtsdatum, geschlecht, mitgliedsnummer, mitglied_id),
        )

        cursor.execute(
            """
            UPDATE adressen
            SET
                strasse = ?,
                hausnummer = ?,
                plz = ?,
                ort = ?
            WHERE
                id = (
                    SELECT
                        adresse_id
                    FROM
                        mitglieder
                    WHERE
                        id = ?
                )
            """,
            (strasse, hausnummer, plz, ort, mitglied_id),
        )

        cursor.execute(
            """
            UPDATE erziehungsberechtigte
            SET
                vorname = ?,
                nachname = ?,
                email = ?,
                telefon = ?
            WHERE
                id = ?
            """,
            (
                eb_vorname,
                eb_nachname,
                eb_email,
                eb_telefon,
                eb_id,
            ),
        )
